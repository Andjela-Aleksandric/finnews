"""Preuzimanje RSS izvora, čišćenje, upis u arhivu i rangiranje važnosti."""
import hashlib
import html
import json
import time as _time
import urllib.parse
import re
import shutil
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
import requests

import db

APP_DIR = Path(__file__).resolve().parent
DEFAULT_FEEDS = APP_DIR / "feeds.json"
USER_FEEDS = db.DATA_DIR / "feeds.json"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) FinNews/1.0"}

# Ključne reči koje podižu važnost vesti (težina se sabira, max 3 pogotka po grupi)
KEYWORDS = {
    "federal reserve": 3, "fed": 3, "fomc": 3, "powell": 2.5, "ecb": 3, "lagarde": 2,
    "bank of england": 2, "bank of japan": 2, "pboc": 2, "central bank": 2, "rate cut": 3,
    "rate hike": 3, "interest rate": 2, "inflation": 2.5, "cpi": 2.5, "pce": 2,
    "jobs report": 2.5, "payrolls": 2.5, "unemployment": 1.5, "gdp": 2, "recession": 2.5,
    "treasury": 1.5, "yield": 1.5, "bond": 1, "dollar": 1, "euro": 1, "oil": 1.2, "opec": 1.5,
    "gold": 1, "tariff": 2, "sanction": 1.5, "earnings": 1.5, "guidance": 1, "profit warning": 2,
    "s&p 500": 1.5, "nasdaq": 1.2, "dow": 1, "stoxx": 1, "volatility": 1.2, "vix": 1.5,
    "selloff": 2, "sell-off": 2, "crash": 2.5, "rally": 1, "record high": 1.5, "bankruptcy": 2,
    "default": 2, "downgrade": 1.5, "merger": 1.5, "acquisition": 1.5, "ipo": 1, "etf": 1,
    "private credit": 1.5, "hedge fund": 1, "portfolio": 1, "bitcoin": 1, "stablecoin": 1,
    "regulator": 1, "sec": 1, "nvidia": 1, "apple": 0.8, "microsoft": 0.8,
    "nbs": 2, "narodna banka": 2, "referentn": 2, "belex": 1.5, "inflacij": 2, "kamatn": 1.5,
}
# Za istraživanja: teme bliske računarskoj inteligenciji u finansijama i portfoliju
RESEARCH_KW = {
    "machine learning": 2, "deep learning": 2, "neural": 2, "fuzzy": 2.5, "anfis": 3,
    "neuro-fuzzy": 3, "reinforcement learning": 2, "large language": 1.5, "llm": 1.5,
    "transformer": 1.5, "genetic algorithm": 1.5, "portfolio": 2, "asset pricing": 2,
    "factor": 1, "volatility": 1.5, "forecast": 1.5, "risk": 1, "option pricing": 1.2,
    "optimization": 1, "cryptocurrenc": 1, "market efficiency": 1.5, "anomal": 1.2,
}
# Težine izdavača za vesti iz Google News (arhiva 6 meseci)
TOP_PUBLISHERS = {
    "Reuters": 1.6, "Bloomberg": 1.6, "Bloomberg.com": 1.6, "Financial Times": 1.6,
    "The Wall Street Journal": 1.5, "WSJ": 1.5, "The Economist": 1.4, "Barron's": 1.2,
    "CNBC": 1.1, "MarketWatch": 1.1, "Yahoo Finance": 0.9, "Federal Reserve": 2.0,
    "European Central Bank": 2.0, "Associated Press": 1.1, "AP News": 1.1, "Axios": 1.0,
    "Bloomberg Adria": 1.4, "rs.bloombergadria.com": 1.4, "Nova ekonomija": 1.1, "Forbes": 0.8,
    "RTS": 1.3, "N1 Info": 1.2, "N1": 1.2, "Politika": 1.1, "Danas": 1.1, "Vreme": 1.1, "BBC News na srpskom": 1.2,
    "BBC": 1.4, "BBC News": 1.4, "The Guardian": 1.3, "AP": 1.3, "The New York Times": 1.4, "The Washington Post": 1.3,
    "Politico": 1.2, "POLITICO": 1.2, "Politico Europe": 1.2, "DW": 1.2, "Al Jazeera English": 1.1, "France 24": 1.1,
}
GENERAL_KW = {
    "vlad": 1.5, "skupštin": 1.5, "izbor": 2, "predsednik": 1.5, "premijer": 1.5, "ministar": 1, "protest": 1.5,
    "zakon": 1, "eu ": 1, "evropsk": 1, "kosov": 1.5, "rusij": 1, "kin": 0.5, "nato": 1.5, "rat": 1.5,
    "election": 2, "president": 1.5, "government": 1.5, "parliament": 1.5, "prime minister": 1.5, "war": 2,
    "ceasefire": 2, "sanction": 1.5, "summit": 1.5, "ukraine": 1.5, "russia": 1.5, "gaza": 1.5, "israel": 1.5,
    "china": 1, "trump": 1, "court": 1, "attack": 1.5, "earthquake": 2, "crisis": 1.5,
}
BACKFILL_QUERIES = [
    ("site:reuters.com markets OR economy OR stocks", "Vesti", "en"),
    ("site:bloomberg.com markets OR economy", "Vesti", "en"),
    ("site:ft.com markets OR economy", "Vesti", "en"),
    ("site:wsj.com markets OR economy", "Vesti", "en"),
    ("Federal Reserve OR ECB interest rate decision", "Centralne banke i makro", "en"),
    ("inflation OR recession OR GDP OR jobs report", "Centralne banke i makro", "en"),
    ("stock market selloff OR rally OR record high", "Vesti", "en"),
    ("\"Narodna banka Srbije\" OR \"Beogradska berza\" OR BELEX OR \"referentna kamatna stopa\"", "Srbija i region", "sr"),
]
STOP = set("""a an the of to in on for and or with by at from as is are was be its it that this
after over into amid says say said new up down vs""".split())


FEEDS_VERSION = 3  # povećaj kad se dodaju novi podrazumevani izvori


def load_feeds():
    if not USER_FEEDS.exists():
        db.DATA_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(DEFAULT_FEEDS, USER_FEEDS)  # bez kopiranja dozvola (izvorni fajl može biti samo za čitanje)
    feeds = json.loads(USER_FEEDS.read_text(encoding="utf-8"))
    marker = db.DATA_DIR / f"feeds_v{FEEDS_VERSION}.done"
    if not marker.exists():  # dodaj nove podrazumevane izvore i postojećoj listi (jednom)
        have = {f["url"] for f in feeds}
        feeds += [f for f in json.loads(DEFAULT_FEEDS.read_text(encoding="utf-8")) if f["url"] not in have]
        save_feeds(feeds)
        marker.write_text("ok")
    return feeds


def save_feeds(feeds):
    import os
    import stat
    try:
        if USER_FEEDS.exists():
            os.chmod(USER_FEEDS, USER_FEEDS.stat().st_mode | stat.S_IWUSR)
        USER_FEEDS.write_text(json.dumps(feeds, ensure_ascii=False, indent=2), encoding="utf-8")
    except PermissionError:  # ako ni to ne uspe, zameni fajl novim
        tmp = USER_FEEDS.with_suffix(".tmp")
        tmp.write_text(json.dumps(feeds, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, USER_FEEDS)


def clean(text, limit=1500):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def parse_date(entry):
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except (TypeError, ValueError):
                pass
    return datetime.now(timezone.utc)


def _download(url):
    if url.startswith("file://") or Path(url).exists():
        return Path(url.replace("file://", "")).read_bytes()
    r = requests.get(url, headers=UA, timeout=20)
    r.raise_for_status()
    return r.content


def scrape_html(feed, raw):
    """Za sajtove bez RSS-a: naslovi i linkovi članaka sa naslovne strane (isti domen, dovoljno dug naslov)."""
    from html.parser import HTMLParser
    from urllib.parse import urljoin, urlparse
    base = feed["url"]
    host = urlparse(base).netloc

    class P(HTMLParser):
        def __init__(self):
            super().__init__()
            self.href, self.buf, self.out = None, [], []

        def handle_starttag(self, tag, attrs):
            if tag == "a":
                self.href, self.buf = dict(attrs).get("href"), []

        def handle_data(self, data):
            if self.href:
                self.buf.append(data)

        def handle_endtag(self, tag):
            if tag == "a" and self.href:
                self.out.append((self.href, " ".join("".join(self.buf).split())))
                self.href = None

    p = P()
    p.feed(raw.decode("utf-8", "ignore"))
    now = datetime.now(timezone.utc)
    seen, out = set(), []
    for href, text in p.out:
        url = urljoin(base, href or "")
        u = urlparse(url)
        if u.netloc != host or len([x for x in u.path.split("/") if x]) < 2 or not (35 <= len(text) <= 220):
            continue
        if url in seen:
            continue
        seen.add(url)
        out.append({"id": hashlib.sha1(url.encode()).hexdigest()[:16], "source": feed["name"],
                    "category": feed.get("category", "Vesti"), "lang": feed.get("lang", "sr"), "title": text, "link": url,
                    "summary": "", "published": now.isoformat(timespec="seconds"),
                    "fetched_at": now.isoformat(timespec="seconds"), "base": float(feed.get("weight", 1.0))})
    if not out:
        raise ValueError("Na stranici nisu pronađeni članci")
    return out[:40]


def fetch_feed(feed):
    raw = _download(feed["url"])
    if feed.get("type") == "html":
        return scrape_html(feed, raw)
    parsed = feedparser.parse(raw)
    if parsed.bozo and not parsed.entries:
        raise ValueError(f"Neispravan RSS: {parsed.bozo_exception}")
    now = datetime.now(timezone.utc)
    out = []
    for e in parsed.entries:
        link = e.get("link") or ""
        title = clean(e.get("title"), 400)
        if not title or not link:
            continue
        suffix = feed.get("strip_suffix")
        if suffix and title.endswith(suffix):
            title = title[: -len(suffix)].strip()
        src_name = feed["name"]
        if feed.get("gnews"):  # Google News: pravi izvor je u <source>, a naslov se završava sa " - Izvor"
            pub_src = (e.get("source") or {}).get("title")
            if pub_src:
                src_name = pub_src
                if title.endswith(" - " + pub_src):
                    title = title[: -len(pub_src) - 3].strip()
        summary = clean(e.get("summary") or e.get("description"), 3000 if feed.get("category") == "Istraživanja" else 1500)
        if feed.get("category") == "Istraživanja":  # arXiv dodaje "arXiv:id Announce Type: new Abstract:"
            summary = re.sub(r"^arXiv:\S+\s+Announce Type:\s*\S+\s*(Abstract:\s*)?", "", summary)
        if summary.lower().startswith(title.lower()[:40].lower()) and len(summary) < len(title) + 40:
            summary = ""  # Google News ponavlja naslov u opisu
        pub = parse_date(e)
        if pub > now + timedelta(hours=1):
            pub = now
        out.append({
            "id": hashlib.sha1(link.encode()).hexdigest()[:16],
            "source": src_name, "category": feed.get("category", "Vesti"),
            "lang": feed.get("lang", "en"), "title": title, "link": link, "summary": summary,
            "published": pub.isoformat(timespec="seconds"),
            "fetched_at": now.isoformat(timespec="seconds"),
            "base": float(feed.get("weight", 1.0)),
        })
    return out


def keyword_score(text):
    text = " " + text.lower() + " "
    s = 0.0
    for kw, w in KEYWORDS.items():
        if len(kw) <= 4:
            if re.search(r"\b" + re.escape(kw) + r"\b", text):
                s += w
        elif kw in text:
            s += w
    return min(s, 9.0)


def tokens(title):
    return {w for w in re.findall(r"[a-zA-Zčćšžđ0-9&]+", title.lower()) if w not in STOP and len(w) > 2}


def research_score(text):
    text = text.lower()
    return min(sum(w for kw, w in RESEARCH_KW.items() if kw in text), 9.0)


def source_weight(feeds, name):
    if name in feeds:
        return float(feeds[name].get("weight", 1.0))
    return TOP_PUBLISHERS.get(name, 0.8)


def rescore(con, hours=72, start=None, end=None):
    """Važnost = težina izvora + ključne reči + koliko različitih izvora piše o istoj temi."""
    start = start or (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat(timespec="seconds")
    end = end or "9999"
    feeds = {f["name"]: f for f in load_feeds()}
    rows = [dict(r) for r in con.execute(
        "SELECT id, source, category, title, summary FROM items WHERE published >= ? AND published < ?",
        (start, end))]
    toks = [tokens(r["title"]) for r in rows]
    for i, r in enumerate(rows):
        others = set()
        if r["category"] != "Istraživanja" and toks[i]:
            for j, r2 in enumerate(rows):
                if j == i or r2["source"] == r["source"] or not toks[j]:
                    continue
                inter = len(toks[i] & toks[j])
                if inter >= 3 and inter / len(toks[i] | toks[j]) >= 0.25:
                    others.add(r2["source"])
        base = source_weight(feeds, r["source"])
        text = r["title"] + " " + (r["summary"] or "")[:400]
        if r["category"] == "Istraživanja":
            score = base * 2 + research_score(text)
        elif r["category"] in ("Srbija", "Svet"):
            low = " " + text.lower() + " "
            gk = min(sum(w for kw, w in GENERAL_KW.items() if kw in low), 6.0)
            score = base * 2 + gk + 2.2 * min(len(others), 5)
        else:
            score = base * 2 + keyword_score(text) + 1.8 * min(len(others), 4)
        con.execute("UPDATE items SET score=? WHERE id=?", (round(score, 2), r["id"]))
    con.commit()


def fetch_all(con=None):
    con = con or db.connect()
    feeds = [f for f in load_feeds() if f.get("enabled", True)]
    results = {}

    def work(f):
        try:
            return f, fetch_feed(f), None
        except Exception as ex:  # noqa: BLE001 - jedan loš izvor ne sme da obori ostale
            return f, [], str(ex)[:300]

    with ThreadPoolExecutor(max_workers=8) as pool:
        for f, items, err in pool.map(work, feeds):
            results[f["name"]] = (items, err)

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    new = 0
    for name, (items, err) in results.items():
        for it in items:
            cur = con.execute(
                "INSERT OR IGNORE INTO items(id, source, category, lang, title, link, summary, "
                "published, fetched_at) VALUES(?,?,?,?,?,?,?,?,?)",
                (it["id"], it["source"], it["category"], it["lang"], it["title"], it["link"],
                 it["summary"], it["published"], it["fetched_at"]))
            new += cur.rowcount
        if err:
            con.execute("INSERT INTO fetch_log(source, last_error) VALUES(?, ?) "
                        "ON CONFLICT(source) DO UPDATE SET last_error=excluded.last_error",
                        (name, f"{now}: {err}"))
        else:
            con.execute("INSERT INTO fetch_log(source, last_ok, last_error, last_count) VALUES(?,?,NULL,?) "
                        "ON CONFLICT(source) DO UPDATE SET last_ok=excluded.last_ok, last_error=NULL, "
                        "last_count=excluded.last_count", (name, now, len(items)))
    con.commit()
    rescore(con)
    db.set_meta(con, "last_fetch", now)
    errors = {k: v[1] for k, v in results.items() if v[1]}
    return {"new": new, "sources": len(feeds), "errors": errors}


# ---------- arhiva: najvažnije vesti iz prethodnih meseci ----------
def gnews_url(query, d1, d2, lang):
    hl, gl, ceid = ("sr", "RS", "RS:sr") if lang == "sr" else ("en-US", "US", "US:en")
    q = urllib.parse.quote_plus(f"{query} after:{d1} before:{d2}")
    return f"https://news.google.com/rss/search?q={q}&hl={hl}&gl={gl}&ceid={ceid}"


def parse_gnews(raw, category, lang):
    parsed = feedparser.parse(raw)
    now = datetime.now(timezone.utc)
    out = []
    for e in parsed.entries:
        link, title = e.get("link") or "", clean(e.get("title"), 400)
        if not link or not title:
            continue
        src = (e.get("source") or {}).get("title") or "Google News"
        if title.endswith(" - " + src):
            title = title[: -len(src) - 3].strip()
        out.append({
            "id": hashlib.sha1(link.encode()).hexdigest()[:16], "source": src, "category": category,
            "lang": lang, "title": title, "link": link, "summary": "",
            "published": parse_date(e).isoformat(timespec="seconds"),
            "fetched_at": now.isoformat(timespec="seconds"),
        })
    return out


def backfill(con=None, months=6, progress=None):
    """Za svaku nedelju u poslednjih N meseci uzima najvažnije vesti velikih medija (Google News),
    upisuje ih u arhivu i rangira unutar nedelje."""
    con = con or db.connect()
    today = datetime.now(timezone.utc).date()
    weeks = []
    d = today - timedelta(days=int(months * 30.5))
    while d < today:
        weeks.append((d, min(d + timedelta(days=7), today + timedelta(days=1))))
        d += timedelta(days=7)
    tasks = [(w, q) for w in weeks for q in BACKFILL_QUERIES]
    done, new, errors = 0, 0, 0

    def work(task):
        (d1, d2), (query, cat, lang) = task
        try:
            _time.sleep(0.3)
            return parse_gnews(_download(gnews_url(query, d1.isoformat(), d2.isoformat(), lang)), cat, lang), None
        except Exception as ex:  # noqa: BLE001
            return [], str(ex)

    with ThreadPoolExecutor(max_workers=4) as pool:
        for items, err in pool.map(work, tasks):
            done += 1
            errors += bool(err)
            for it in items:
                cur = con.execute(
                    "INSERT OR IGNORE INTO items(id, source, category, lang, title, link, summary, "
                    "published, fetched_at) VALUES(?,?,?,?,?,?,?,?,?)",
                    (it["id"], it["source"], it["category"], it["lang"], it["title"], it["link"],
                     it["summary"], it["published"], it["fetched_at"]))
                new += cur.rowcount
            if progress:
                progress(done / len(tasks))
    con.commit()
    for d1, d2 in weeks:
        rescore(con, start=datetime.combine(d1, datetime.min.time(), timezone.utc).isoformat(timespec="seconds"),
                end=datetime.combine(d2, datetime.min.time(), timezone.utc).isoformat(timespec="seconds"))
    rescore(con)
    if errors < len(tasks):
        db.set_meta(con, "backfill_done", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    return {"new": new, "requests": len(tasks), "errors": errors}


def relevance(item, now=None, half_life_h=18.0):
    """Relevantnost = važnost (izvor + ključne reči + broj izvora) x svežina (eksponencijalno opadanje)."""
    now = now or datetime.now(timezone.utc)
    try:
        age_h = max(0.0, (now - datetime.fromisoformat(item["published"])).total_seconds() / 3600)
    except (TypeError, ValueError):
        age_h = 48.0
    return (item.get("score") or 0.0) * (0.35 + 0.65 * 0.5 ** (age_h / half_life_h))
