"""Preuzimanje punog teksta članka za čitanje u aplikaciji.
Sajtovi sa paywall-om se ne zaobilaze - za njih se koristi opis iz RSS-a."""
from datetime import datetime, timedelta, timezone

import re
import urllib.parse

import feedparser
import requests

import db
import fetcher

PAYWALL = ("ft.com", "wsj.com", "bloomberg.com", "economist.com", "barrons.com", "nytimes.com", "washingtonpost.com")
PAYWALL_SOURCES = ("Financial Times", "WSJ", "The Wall Street Journal", "Bloomberg", "The Economist", "Barron's")
ABSTRACT_SOURCES = ("arXiv", "NBER", "BIS Working")
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) "
                         "Version/17.0 Safari/605.1.15",
           "Accept-Language": "en-US,en;q=0.9,sr;q=0.8"}
MIN_OK = 700
# Besplatni izvori koji objavljuju ceo tekst (Yahoo Finance često prenosi Bloomberg/Reuters u celosti)
FREE_HINT = ("Yahoo", "CNBC", "AP News", "Associated Press", "The Guardian", "BBC", "CNN", "Axios", "Investing.com",
             "Reuters", "MarketWatch", "Fox Business", "Forbes", "Euronews", "DW", "NPR", "Business Insider",
             "Morningstar", "Kitco", "TheStreet", "Benzinga", "Motley Fool", "FXStreet", "Al Jazeera", "Fortune")


def _resolve(url):
    if "news.google.com" not in url:
        return url
    try:
        from googlenewsdecoder import gnewsdecoder
        res = gnewsdecoder(url, interval=0)
        if res.get("status"):
            return res["decoded_url"]
    except Exception:  # noqa: BLE001
        pass
    return url


def is_paywalled(item, url=""):
    return any(d in url for d in PAYWALL) or any((item.get("source") or "").startswith(s) for s in PAYWALL_SOURCES)


def _similar(a, b):
    ta, tb = fetcher.tokens(a), fetcher.tokens(b)
    return len(ta & tb) / max(1, len(ta | tb)) if ta and tb else 0.0


def _extract(url):
    import trafilatura
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return trafilatura.extract(r.text, include_comments=False, include_tables=False, favor_recall=True) or ""


def find_free_version(con, item):
    """Traži istu vest kod besplatnog izvora: prvo u arhivi, zatim preko Google News pretrage."""
    # 1) arhiva - ista tema u ±2 dana od izvora koji nisu iza paywall-a
    from datetime import datetime as _dt, timedelta as _td
    pub = _dt.fromisoformat(item["published"])
    rows = con.execute("SELECT * FROM items WHERE published BETWEEN ? AND ? AND category != 'Istraživanja' "
                       "AND id != ? LIMIT 800", ((pub - _td(days=2)).isoformat(timespec="seconds"),
                                                 (pub + _td(days=2)).isoformat(timespec="seconds"), item["id"])).fetchall()
    cands = sorted(((_similar(item["title"], r["title"]), dict(r)) for r in rows), key=lambda x: -x[0])
    for sim, r in cands[:10]:
        if sim < 0.3 or is_paywalled(r, r["link"]):
            continue
        try:
            url = _resolve(r["link"])
            if is_paywalled(r, url):
                continue
            text = _extract(url)
            if len(text) >= MIN_OK:
                return text, url, r["source"]
        except Exception:  # noqa: BLE001
            continue
    # 2) Google News - ključne reči iz naslova
    words = [w for w in re.findall(r"[A-Za-z0-9&'.-]+", item["title"]) if w.lower() not in fetcher.STOP and len(w) > 2][:8]
    if not words:
        return None
    q = urllib.parse.quote_plus(" ".join(words) + " when:4d")
    try:
        feed = feedparser.parse(requests.get(f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en",
                                             headers=HEADERS, timeout=15).content)
    except Exception:  # noqa: BLE001
        return None
    scored = []
    for e in feed.entries[:40]:
        src = (e.get("source") or {}).get("title") or ""
        title = re.sub(r"\s+-\s+[^-]+$", "", e.get("title") or "")
        if any(src.startswith(p) for p in PAYWALL_SOURCES) or any(d in (e.get("source") or {}).get("href", "") for d in PAYWALL):
            continue
        sim = _similar(item["title"], title)
        if sim >= 0.25:
            scored.append((sim + (0.15 if any(src.startswith(f) for f in FREE_HINT) else 0), src, e.get("link")))
    for _, src, link in sorted(scored, reverse=True)[:8]:
        try:
            url = _resolve(link)
            if any(d in url for d in PAYWALL):
                continue
            text = _extract(url)
            if len(text) >= MIN_OK:
                return text, url, src
        except Exception:  # noqa: BLE001
            continue
    return None


FULL = ("ok", "abstract")


def is_full(status):
    """Da li je sačuvan ceo tekst (originalni ili iz drugog, besplatnog izvora)."""
    return bool(status) and (status in FULL or status.startswith("alt:"))


def statuses(con, ids):
    if not ids:
        return {}
    q = ",".join("?" * len(ids))
    return {r["item_id"]: r["status"] for r in con.execute(f"SELECT item_id, status FROM articles WHERE item_id IN ({q})", list(ids))}


def get_article(con, item, force=False):
    """Vraća dict: text, status, url. Status 'ok' ili 'alt:<izvor>' znači ceo tekst; 'partial' znači da ceo tekst
    nije pronađen ni na originalu ni kod drugih izvora (tada se vest ne prikazuje kao pročitana)."""
    cached = db.get_article(con, item["id"])
    if cached and not force and (is_full(cached["status"]) or _fresh(cached)):
        return cached
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    url = item["link"]
    text, status = "", "partial"
    if item.get("category") == "Istraživanja" or any((item.get("source") or "").startswith(s) for s in ABSTRACT_SOURCES):
        text, status = item.get("summary") or "", "abstract"
    else:
        try:
            if not is_paywalled(item, url):
                url = _resolve(url)
            if not is_paywalled(item, url):
                got = _extract(url)
                if len(got) >= MIN_OK:
                    text, status = got, "ok"
        except Exception:  # noqa: BLE001
            pass
        if status != "ok":  # original nije dostupan u celosti -> traži istu vest kod drugih izvora
            try:
                alt = find_free_version(con, item)
            except Exception:  # noqa: BLE001
                alt = None
            if alt:
                text, url, status = alt[0], alt[1], "alt:" + alt[2]
            else:
                text = item.get("summary") or ""
    db.save_article(con, item["id"], url, text, status, now)
    return {"item_id": item["id"], "url": url, "text": text, "status": status, "fetched_at": now}


def _fresh(cached, hours=6):
    """Neuspeli pokušaj se ponavlja tek posle nekoliko sati (možda se u međuvremenu pojavi besplatna verzija)."""
    try:
        return datetime.now(timezone.utc) - datetime.fromisoformat(cached["fetched_at"]) < timedelta(hours=hours)
    except (TypeError, ValueError):
        return False


# ---------- naučni radovi: abstract + zaključak + pravci za dalja istraživanja ----------
FUTURE_KW = ("future research", "future work", "further research", "future studies", "future direction",
             "limitation", "could be extended", "can be extended", "open question", "remains open",
             "promising direction", "left for future", "warrant further", "worth exploring")
CONCL_HEAD = re.compile(r"\n\s*(?:\d+(?:\.\d+)?\.?\s+|[IVX]+\.\s+)?(conclusions?|concluding remarks|summary and conclusions?|"
                        r"discussion and conclusions?|conclusions? and future (?:work|research)|conclusion and discussion)"
                        r"\s*\n", re.I)
END_HEAD = re.compile(r"\n\s*(references|bibliography|acknowledg(?:e)?ments?|appendix|declaration of|data availability|"
                      r"credit authorship|funding)\b", re.I)


def _arxiv_id(*urls):
    for u in urls:
        m = re.search(r"(?:arxiv\.org/(?:abs|pdf|html)/|10\.48550/arxiv\.)(\d{4}\.\d{4,5})", u or "", re.I)
        if m:
            return m.group(1)
    return None


def clean_abstract(text):
    text = re.sub(r"^arXiv:\S+\s+Announce Type:\s*\S+\s*", "", text or "")
    return re.sub(r"^\s*Abstract:\s*", "", text).strip()


def _pdf_text(url):
    from io import BytesIO
    from pypdf import PdfReader
    r = requests.get(url, headers=HEADERS, timeout=40)
    r.raise_for_status()
    if b"%PDF" not in r.content[:1024]:
        raise ValueError("not a pdf")
    reader = PdfReader(BytesIO(r.content[:30_000_000]))
    pages = [pg.extract_text() or "" for pg in reader.pages[:60]]
    text = "\n".join(pages)
    text = re.sub(r"-\n(?=[a-z])", "", text)          # spoji reči prelomljene crticom
    return text


def _conclusion(full):
    heads = list(CONCL_HEAD.finditer(full))
    if not heads:
        return ""
    start = heads[-1].end() if len(heads) > 1 and heads[-1].start() > len(full) * 0.5 else heads[0].end()
    end = END_HEAD.search(full, start)
    body = full[start: end.start() if end else start + 8000]
    body = re.sub(r"(?<![.!?:])\n(?!\n)", " ", body)  # spoji redove unutar pasusa
    return re.sub(r"[ \t]+", " ", body).strip()[:7000]


def future_sentences(text):
    sents = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text or ""))
    return [s.strip() for s in sents if any(k in s.lower() for k in FUTURE_KW) and 40 < len(s) < 500][:6]


def get_paper(con, p, force=False):
    """p: rad iz OpenAlex-a (abstract, pdf_url) ili arXiv/NBER stavka (summary, link).
    Vraća dict: abstract, conclusion, future, status ('full' | 'abstract'), pdf."""
    abstract = clean_abstract(p.get("abstract") or p.get("summary") or "")
    cached = db.get_article(con, p["id"])
    if cached and not force and cached["status"] in ("concl", "noconcl", "nooa"):
        concl = cached["text"] if cached["status"] == "concl" else ""
        return {"abstract": abstract, "conclusion": concl, "future": future_sentences(concl or abstract),
                "status": "full" if concl else "abstract", "pdf": cached["url"]}
    aid = _arxiv_id(p.get("link"), p.get("pdf_url"), p.get("id"))
    pdf = p.get("pdf_url") or (f"https://arxiv.org/pdf/{aid}" if aid else None)
    if not pdf and "nber.org/papers/" in (p.get("link") or ""):
        num = re.search(r"papers/(w\d+)", p["link"])
        pdf = f"https://www.nber.org/system/files/working_papers/{num.group(1)}/{num.group(1)}.pdf" if num else None
    concl, status = "", "nooa"
    if pdf:
        try:
            concl = _conclusion(_pdf_text(pdf))
            status = "concl" if len(concl) > 200 else "noconcl"
        except Exception:  # noqa: BLE001
            status = "nooa"
    db.save_article(con, p["id"], pdf or "", concl, status, datetime.now(timezone.utc).isoformat(timespec="seconds"))
    return {"abstract": abstract, "conclusion": concl, "future": future_sentences(concl or abstract),
            "status": "full" if concl else "abstract", "pdf": pdf}


RESULT_KW = ("we find", "we show", "results show", "results indicate", "results suggest", "our results", "findings",
             "outperform", "significantly", "improves", "improvement", "reduces", "increases", "evidence",
             "we document", "demonstrate", "achieves", "higher", "lower", "accuracy", "sharpe", "return")


def result_sentences(text, n=2):
    """Bez AI: rečenice koje najverovatnije nose rezultat (cue reči, brojevi, procenti)."""
    sents = [x.strip() for x in re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text or "")) if 30 < len(x) < 400]
    if not sents:
        return ""
    def score(x):
        lx = x.lower()
        return (sum(k in lx for k in RESULT_KW) * 2 + len(re.findall(r"\d+(?:\.\d+)?\s*%|\d+\.\d+", x))
                + (1 if lx.startswith(("we find", "results", "our results", "the results")) else 0))
    best = sorted(range(len(sents)), key=lambda i: (-score(sents[i]), -i))[:n]
    return " ".join(sents[i] for i in sorted(best))
