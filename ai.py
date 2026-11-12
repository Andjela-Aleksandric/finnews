"""Prevod i sažeci. Sa Anthropic API ključem koristi Claude; bez ključa radi osnovni režim
(besplatan Google prevod preko deep-translator + ekstraktivni sažetak)."""
import json
import os
import re
from collections import Counter

import db

CONFIG = db.DATA_DIR / "config.json"
FAST_MODEL = "claude-haiku-5-5"     # prevod, kratka objašnjenja
SMART_MODEL = "claude-sonnet-5-5"   # dnevni brief

CYR = "абвгдђежзијклљмнњопрстћуфхцчџшАБВГДЂЕЖЗИЈКЛЉМНЊОПРСТЋУФХЦЧЏШ"
LAT = ["a", "b", "v", "g", "d", "đ", "e", "ž", "z", "i", "j", "k", "l", "lj", "m", "n", "nj", "o", "p",
       "r", "s", "t", "ć", "u", "f", "h", "c", "č", "dž", "š",
       "A", "B", "V", "G", "D", "Đ", "E", "Ž", "Z", "I", "J", "K", "L", "Lj", "M", "N", "Nj", "O", "P",
       "R", "S", "T", "Ć", "U", "F", "H", "C", "Č", "Dž", "Š"]
CYR2LAT = dict(zip(CYR, LAT))


def to_latin(s):
    return "".join(CYR2LAT.get(ch, ch) for ch in s or "")


# ---------- podešavanja ----------
def load_config():
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_config(cfg):
    db.DATA_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    try:
        os.chmod(CONFIG, 0o600)
    except OSError:
        pass


def api_key():
    return os.environ.get("ANTHROPIC_API_KEY") or load_config().get("anthropic_api_key")


def has_key():
    return bool(api_key())


def script():
    return load_config().get("sr_script", "latinica")


OLLAMA = "http://localhost:11434"


def ollama_model():
    return load_config().get("ollama_model") or "gemma3:12b"


def ollama_on():
    """Lokalni AI (Ollama) - besplatan, radi na tvom Mac-u, bez ključa i bez slanja podataka napolje."""
    import requests
    try:
        r = requests.get(f"{OLLAMA}/api/tags", timeout=1.5)
        names = [m.get("name", "") for m in r.json().get("models", [])]
        return any(n == ollama_model() or n.split(":")[0] == ollama_model().split(":")[0] for n in names)
    except Exception:  # noqa: BLE001
        return False


def llm_on():
    return has_key() or ollama_on()


def llm_name():
    return "Claude" if has_key() else (f"lokalni AI ({ollama_model()})" if ollama_on() else "")


def _ollama(prompt, max_tokens=2000):
    import requests
    r = requests.post(f"{OLLAMA}/api/chat", timeout=600, json={
        "model": ollama_model(), "stream": False,
        "messages": [{"role": "user", "content": prompt}],
        "options": {"num_ctx": 16384, "num_predict": max_tokens, "temperature": 0.3}})
    r.raise_for_status()
    out = r.json().get("message", {}).get("content", "")
    return re.sub(r"<think>.*?</think>", "", out, flags=re.S).strip()


def _claude(prompt, model=FAST_MODEL, max_tokens=4000):
    """Generativni AI: Claude ako postoji ključ, inače lokalni model preko Ollame."""
    if not has_key():
        out = _ollama(prompt, max_tokens)
        return to_latin(out) if script() != "ćirilica" and re.search("[а-яА-ЯђћџљњЂЋЏЉЊ]", out) else out
    import anthropic
    client = anthropic.Anthropic(api_key=api_key())
    msg = client.messages.create(model=model, max_tokens=max_tokens,
                                 messages=[{"role": "user", "content": prompt}])
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()


def _lang_instr(lang):
    if lang == "sr":
        return ("srpski jezik, " + ("ćirilica" if script() == "ćirilica" else "latinica") +
                ". Koristi ustaljenu srpsku finansijsku terminologiju; engleski termin dodaj u zagradi samo "
                "kad srpski nije ustaljen. Koristi kratku crtu (-), nikad dugu (—).")
    return "English. Use a short hyphen (-) instead of em-dashes."


# ---------- prevod ----------
def translate_items(pairs, lang):
    """pairs: lista (naslov, opis). Vraća listu (naslov, opis) na ciljnom jeziku."""
    if not pairs:
        return []
    if has_key():
        out = []
        for i in range(0, len(pairs), 15):
            chunk = pairs[i:i + 15]
            try:
                out += _claude_translate(chunk, lang)
            except Exception:  # noqa: BLE001
                out += _free_translate(chunk, lang)
        return out
    return _free_translate(pairs, lang)


def _claude_translate(chunk, lang):
    data = [{"t": t, "s": (s or "")[:700]} for t, s in chunk]
    prompt = (f"Translate these financial news items into {_lang_instr(lang)}\n"
              "Keep tickers, company names, numbers and currencies unchanged. "
              "Return ONLY a JSON array of objects {\"t\": title, \"s\": summary}, same order and length.\n\n"
              + json.dumps(data, ensure_ascii=False))
    text = _claude(prompt)
    arr = json.loads(text[text.find("["): text.rfind("]") + 1])
    if len(arr) != len(chunk):
        raise ValueError("length mismatch")
    res = [(a.get("t", ""), a.get("s", "")) for a in arr]
    if lang == "sr" and script() != "ćirilica":
        res = [(to_latin(t), to_latin(s)) for t, s in res]
    return res


LAST_ERROR = None  # poslednja greška besplatnog prevoda (prikazuje se u aplikaciji)
GT_URL = "https://translate.googleapis.com/translate_a/single"
GT_MANY = ["https://translate.googleapis.com/translate_a/t", "https://clients5.google.com/translate_a/t"]
_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
_SESSION = None
_MANY_OFF_UNTIL = 0.0  # ako servis za više tekstova odjednom ne radi, privremeno se ne koristi


def _session():
    global _SESSION
    if _SESSION is None:
        import requests
        _SESSION = requests.Session()
        _SESSION.headers.update({"User-Agent": _UA})
    return _SESSION


def _post(url, params, data, timeout=20, tries=3):
    """POST sa ponavljanjem: Google povremeno vrati 429/5xx ili prekine vezu - tada sačekaj i probaj ponovo."""
    import time as _t
    last = None
    for i in range(tries):
        try:
            r = _session().post(url, params=params, data=data, timeout=timeout)
            if r.status_code in (429, 500, 502, 503, 504):
                raise RuntimeError(f"HTTP {r.status_code}")
            r.raise_for_status()
            return r
        except Exception as ex:  # noqa: BLE001
            last = ex
            if i < tries - 1:
                _t.sleep(0.7 * (2 ** i))
    raise last


def _latin(out, lang):
    return to_latin(out) if lang == "sr" and script() != "ćirilica" else out


def gtx(text, lang):
    """Besplatni Google prevod (isti servis koji koristi Chrome), do ~4500 znakova po pozivu."""
    r = _post(GT_URL, {"client": "gtx", "sl": "auto", "tl": "sr" if lang == "sr" else "en", "dt": "t"}, {"q": text})
    return _latin("".join(seg[0] for seg in r.json()[0] if seg and seg[0]), lang)


def gtx_many(texts, lang):
    """Više tekstova u jednom zahtevu - svaki ostaje zaseban (nema spajanja redova)."""
    import time as _t
    global _MANY_OFF_UNTIL
    if _t.time() < _MANY_OFF_UNTIL:
        raise RuntimeError("multi off")
    err = None
    for url in GT_MANY:
        try:
            r = _post(url, {"client": "gtx", "sl": "auto", "tl": "sr" if lang == "sr" else "en", "format": "text"},
                      [("q", x) for x in texts], tries=2)
            arr = r.json()
            if isinstance(arr, str):
                arr = [arr]
            out = [(x[0] if isinstance(x, list) else x) for x in arr]
            if len(out) == len(texts) and all(isinstance(x, str) for x in out):
                return [_latin(x, lang) for x in out]
            err = ValueError("length mismatch")
        except Exception as ex:  # noqa: BLE001
            err = ex
    _MANY_OFF_UNTIL = _t.time() + 1800
    raise err or RuntimeError("translate failed")


def _fallback_one(text, lang):
    try:
        from deep_translator import GoogleTranslator
        out = GoogleTranslator(source="auto", target="sr" if lang == "sr" else "en").translate(text) or text
        return _latin(out, lang)
    except Exception:  # noqa: BLE001
        return text


def _translate_batch(batch, lang):
    """Vraća listu prevoda iste dužine; redosled pokušaja: više-tekstova -> spojeni redovi -> pojedinačno."""
    try:
        return gtx_many(batch, lang)
    except Exception:  # noqa: BLE001
        pass
    try:
        lines = gtx("\n".join(batch), lang).split("\n")
        if len(lines) == len(batch):
            return [ln.strip() or src for ln, src in zip(lines, batch)]
    except Exception:  # noqa: BLE001
        pass
    from concurrent.futures import ThreadPoolExecutor

    def one(x):
        try:
            return gtx(x, lang)
        except Exception:  # noqa: BLE001
            return _fallback_one(x, lang) if len(batch) <= 12 else x
    with ThreadPoolExecutor(4) as ex:
        return list(ex.map(one, batch))


def _free_translate(pairs, lang):
    """Prevodi listu (naslov, opis) u paketima, paralelno - brzo i za 100+ vesti."""
    global LAST_ERROR
    LAST_ERROR = None
    texts = []
    for t, s_ in pairs:
        texts.append(re.sub(r"\s+", " ", t or "").strip())
        texts.append(re.sub(r"\s+", " ", (s_ or "")[:450]).strip())
    result = list(texts)
    batches, cur, idx, size = [], [], [], 0
    for i, tx in enumerate(texts):
        if not tx:
            continue
        if cur and (size + len(tx) > 3500 or len(cur) >= 60):
            batches.append((cur, idx)); cur, idx, size = [], [], 0
        cur.append(tx); idx.append(i); size += len(tx) + 1
    if cur:
        batches.append((cur, idx))
    from concurrent.futures import ThreadPoolExecutor

    def run(b):
        try:
            return _translate_batch(b[0], lang)
        except Exception as ex:  # noqa: BLE001
            global LAST_ERROR
            LAST_ERROR = str(ex)[:200]
            return b[0]
    with ThreadPoolExecutor(3) as ex:
        outs = list(ex.map(run, batches))
    ok = 0
    for (batch, idx_), out in zip(batches, outs):
        for i, src, tr in zip(idx_, batch, out):
            result[i] = (tr or "").strip() or src
            ok += result[i] != src
    if batches and not ok and not LAST_ERROR:
        LAST_ERROR = "prevod nije vratio rezultat (Google privremeno ograničava zahteve)"
    return [(result[2 * k] or pairs[k][0], result[2 * k + 1] or pairs[k][1]) for k in range(len(pairs))]


def translate_check(lang="sr"):
    """Brza provera prevoda za Podešavanja: vraća (radi?, poruka)."""
    try:
        out = _free_translate([("Stocks rose after the central bank cut interest rates.", "")], lang)[0][0]
        return (out and not out.startswith("Stocks rose")), out
    except Exception as ex:  # noqa: BLE001
        return False, str(ex)


# ---------- sažeci ----------
def extractive_summary(text, n=2):
    sents = re.split(r"(?<=[.!?])\s+", text or "")
    if len(sents) <= n:
        return text or ""
    words = Counter(w for w in re.findall(r"\w{4,}", text.lower()))
    ranked = sorted(range(len(sents)),
                    key=lambda i: -sum(words[w] for w in re.findall(r"\w{4,}", sents[i].lower())))
    return " ".join(sents[i] for i in sorted(ranked[:n]))


def explain_item(item, lang):
    prompt = (f"Odgovori na: {_lang_instr(lang)}\n"
              "Na osnovu naslova i kratkog opisa (pun tekst nije dostupan) objasni vest u 3-5 rečenica: "
              "šta se desilo, zašto je bitno za investitore i portfolio, i koji su mogući efekti na tržišta. "
              "Ne izmišljaj brojke kojih nema u tekstu; ako je opis prekratak, reci šta je nejasno.\n\n"
              f"Izvor: {item['source']}\nNaslov: {item['title']}\nOpis: {item.get('summary') or '-'}")
    return _claude(prompt, FAST_MODEL, 800)


def daily_brief(day, news, research, lang, translations=None):
    if llm_on():
        lines = [f"{i}. [{it['source']}] {it['title']} - {(it.get('summary') or '')[:350]} ({it['link']})"
                 for i, it in enumerate(news, 1)]
        rlines = [f"- [{it['source']}] {it['title']} ({it['link']})" for it in research]
        if lang == "sr":
            head = (f"Ti si iskusan analitičar finansijskih tržišta. Napiši pregled finansijskih vesti za period {day} na jeziku: "
                    f"{_lang_instr('sr')}\nStruktura (markdown naslovi ##): Ukratko (3-5 rečenica - šta je "
                    "najbitnije u ovom periodu), Tržišta, Centralne banke i makro, Kompanije, Srbija i region (samo ako "
                    "ima vesti), Istraživanja vredna pažnje, Šta pratiti narednih dana.\n")
        else:
            head = (f"You are an experienced markets analyst. Write a financial news review for {day} in "
                    f"{_lang_instr('en')}\nStructure (markdown ## headings): In short (3-5 sentences), Markets, "
                    "Central banks & macro, Companies, Serbia & region (only if relevant), Research worth "
                    "reading, What to watch next.\n")
        prompt = (head + "Rules: use ONLY the items below, never invent numbers; merge duplicates across "
                  "sources; cite each point with a markdown link like [Bloomberg](url); be concise, "
                  "bullet points under headings.\n\nNEWS:\n" + "\n".join(lines) +
                  "\n\nRESEARCH:\n" + ("\n".join(rlines) or "-"))
        return _claude(prompt, SMART_MODEL, 3000)

    # osnovni režim bez AI
    translations = translations or {}
    title = "Dnevni pregled" if lang == "sr" else "Daily overview"
    parts = [f"## {title} - {day}",
             "_Osnovni režim: najvažnije vesti po kategorijama. Za pravi AI sažetak dodaj Anthropic API "
             "ključ u Podešavanjima._" if lang == "sr" else
             "_Basic mode: top stories by category. Add an Anthropic API key in Settings for an AI brief._"]
    by_cat = {}
    for it in news + research:
        by_cat.setdefault(it["category"], []).append(it)
    for cat, items in by_cat.items():
        parts.append(f"### {cat}")
        for it in items[:6]:
            t = translations.get(it["id"], {})
            ttl = t.get("title") or it["title"]
            summ = extractive_summary(t.get("summary") or it.get("summary") or "", 1)
            parts.append(f"- **[{ttl}]({it['link']})** ({it['source']})" + (f" - {summ}" if summ else ""))
    return "\n".join(parts)


# ---------- čitanje članaka u aplikaciji ----------
def _chunks(text, size):
    parts, cur = [], ""
    for para in [x for x in (text or "").split("\n") if x.strip()]:
        while len(para) > size:  # predugačak pasus seci po rečenicama
            cut = para.rfind(". ", 0, size)
            cut = cut + 1 if cut > 0 else size
            parts.append(para[:cut]); para = para[cut:].strip()
        if len(cur) + len(para) + 1 > size and cur:
            parts.append(cur); cur = ""
        cur = (cur + "\n" + para).strip()
    if cur:
        parts.append(cur)
    return parts


def summarize_article(title, text, lang):
    """Sažetak u 4-6 tačaka + zašto je bitno. Sa AI (Claude ili lokalni), inače izdvojene rečenice (+ prevod)."""
    if llm_on():
        prompt = (f"Odgovori na: {_lang_instr(lang)}\n"
                  "Sažmi ovaj finansijski članak u 4-6 kratkih tačaka (markdown liste) sa ključnim činjenicama, "
                  "brojevima i imenima. Zatim u jednom pasusu napiši „Zašto je bitno:“ (za investitore i tržišta). "
                  "Koristi samo informacije iz teksta.\n\n"
                  f"NASLOV: {title}\n\nTEKST:\n{text[:14000]}")
        return _claude(prompt, FAST_MODEL, 900)
    sents = extractive_summary(re.sub(r"\s+", " ", text), 5)
    if lang == "sr":
        sents = _free_chunk(sents, "sr")
    return "\n".join("- " + x for x in re.split(r"(?<=[.!?])\s+", sents) if x.strip())


def translate_full(text, lang):
    """Prevod celog članka uz očuvane pasuse."""
    if has_key():
        out = []
        for ch in _chunks(text, 6000):
            prompt = (f"Prevedi ceo tekst ispod na: {_lang_instr(lang)}\n"
                      "Zadrži sve pasuse i prelome redova, ništa ne izostavljaj i ne dodaji. Vrati samo prevod.\n\n" + ch)
            try:
                tr = _claude(prompt, FAST_MODEL, 4000)
            except Exception:  # noqa: BLE001
                tr = _free_chunk(ch, lang)
            out.append(tr)
        res = "\n".join(out)
    else:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(4) as ex:  # delovi teksta se prevode paralelno
            res = "\n".join(ex.map(lambda ch: _free_chunk(ch, lang), _chunks(text, 4000)))
    return to_latin(res) if lang == "sr" and script() != "ćirilica" else res


def _free_chunk(chunk, lang):
    global LAST_ERROR
    try:
        return gtx(chunk, lang)
    except Exception as ex:  # noqa: BLE001
        LAST_ERROR = str(ex)[:200]
        return _fallback_one(chunk, lang)


def analyze_paper(title, abstract, conclusion, lang, thesis=""):
    """Strukturisana analiza rada za istraživača (zahteva API ključ)."""
    prompt = (f"Odgovori na: {_lang_instr(lang)}\n"
              "Ti si mentor na doktorskim studijama iz finansijskog inženjerstva i računarske inteligencije. "
              "Analiziraj rad u kratkim markdown tačkama sa podnaslovima: **Problem**, **Metod**, **Podaci**, "
              "**Glavni rezultati**, **Ograničenja**, **Kako se nadovezuje na moj master rad** (konkretno, 1-3 tačke), "
              "**Ideja za doktorat** (1-2 konkretna pravca). Koristi samo informacije iz teksta; ako nešto ne piše, reci.\n\n"
              f"MOJ MASTER RAD: {thesis}\n\nNASLOV: {title}\n\nABSTRACT: {abstract[:4000]}\n\n"
              f"ZAKLJUČAK: {(conclusion or '-')[:6000]}")
    return _claude(prompt, FAST_MODEL, 1200)


def phd_ideas(thesis, papers, gaps, lang):
    """Predlog tema za doktorat na osnovu master rada, najvažnijih novih studija i praznina u literaturi."""
    plist = "\n".join(f"{i}. {p['title']} ({p.get('venue') or '-'}, {p.get('pub_date') or ''}, {p.get('cited_by', 0)} citata)"
                       f" - {(p.get('abstract') or '')[:500]} [{p.get('link')}]" for i, p in enumerate(papers, 1))
    glist = "\n".join(f"- {g}" for g in gaps[:40]) or "-"
    prompt = (f"Odgovori na: {_lang_instr(lang)}\n"
              "Ti si iskusan mentor na doktorskim studijama (finansijsko inženjerstvo, računarska inteligencija). "
              "Na osnovu mog master rada, najvažnijih studija iz poslednjih 6 meseci i onoga što autori sami navode kao "
              "ograničenja i buduća istraživanja, predloži 5 tema za doktorsku disertaciju koje su NAPREDNI NASTAVAK "
              "mog master rada. Za svaku: ### Naslov, **Istraživačko pitanje**, **Zašto je novo** (koja praznina, uz "
              "link na rad), **Metodologija**, **Podaci** (realno dostupni), **Očekivani doprinos**, **Rizici**. "
              "Na kraju tabela: tema | izvodljivost (1-5) | novina (1-5) | potencijal za objavu (1-5). "
              "Ne izmišljaj radove - citiraj samo sa liste.\n\n"
              f"MOJ MASTER RAD:\n{thesis}\n\nSTUDIJE:\n{plist}\n\nPRAZNINE I BUDUĆA ISTRAŽIVANJA (iz zaključaka):\n{glist}")
    return _claude(prompt, SMART_MODEL, 4000)


def findings(papers, lang):
    """Ključni nalaz svake studije u 1-2 rečenice. papers: dict-ovi sa id, title, abstract (+ conclusion)."""
    if not papers:
        return {}
    if has_key():
        out = {}
        for k in range(0, len(papers), 10):
            chunk = papers[k:k + 10]
            data = [{"id": p["id"], "title": p["title"], "text": ((p.get("abstract") or "") + " " + (p.get("conclusion") or ""))[:2500]}
                    for p in chunk]
            prompt = (f"Za svaku studiju napiši KLJUČNI NALAZ na jeziku: {_lang_instr(lang)} "
                      "Jedna do dve rečenice: šta je konkretno pronađeno (rezultat, sa brojevima ako postoje) i na čemu "
                      "(podaci/metod). Bez uvoda tipa 'Studija istražuje'. Samo iz teksta. "
                      "Vrati SAMO JSON listu objekata {\"id\": ..., \"f\": ...}.\n\n" + json.dumps(data, ensure_ascii=False))
            try:
                txt = _claude(prompt, FAST_MODEL, 2500)
                for o in json.loads(txt[txt.find("["): txt.rfind("]") + 1]):
                    f = o.get("f", "")
                    out[o.get("id")] = to_latin(f) if lang == "sr" and script() != "ćirilica" else f
            except Exception:  # noqa: BLE001
                pass
        return out
    import reader
    raw = [(p["title"], reader.result_sentences((p.get("abstract") or "") + " " + (p.get("conclusion") or ""))) for p in papers]
    if lang == "sr":
        tr = _free_translate([(r[1], "") for r in raw], "sr")
        if LAST_ERROR:
            return {}
        return {p["id"]: tr[i][0] for i, p in enumerate(papers) if raw[i][1]}
    return {p["id"]: raw[i][1] for i, p in enumerate(papers) if raw[i][1]}


def research_review(topic_label, period_label, items, lang):
    """Zbirni pregled oblasti: šta smo naučili u periodu."""
    lst = "\n".join(f"{i}. {p['title']} ({p.get('venue') or '-'}, {p.get('pub_date') or ''}) - NALAZ: {p.get('finding') or '-'} [{p.get('link')}]"
                     for i, p in enumerate(items, 1))
    prompt = (f"Odgovori na: {_lang_instr(lang)}\n"
              f"Napiši pregled istraživanja (research review) za oblast „{topic_label}“ u periodu {period_label}, na "
              "osnovu nalaza studija ispod. Struktura (## naslovi): Glavni zaključci (3-6 tačaka, svaki sa linkom na "
              "studije), Gde se studije slažu, Gde se razilaze ili su rezultati mešoviti, Metode i podaci koji dominiraju, "
              "Otvorena pitanja. Samo iz navedenih nalaza, bez izmišljanja.\n\nSTUDIJE:\n" + lst)
    return _claude(prompt, SMART_MODEL, 2500)


def quick_summary(text, lang, source_lang="en", n=5):
    """Trenutni sažetak: najvažnije rečenice iz teksta (bez AI modela), prevedene ako treba."""
    flat = re.sub(r"\s+", " ", text or "").strip()
    sents = [x for x in re.split(r"(?<=[.!?])\s+", flat) if 40 <= len(x) <= 420]
    if len(sents) > n:
        words = Counter(w for w in re.findall(r"\w{5,}", flat.lower()))
        def sc(i):
            x = sents[i]
            return (sum(words[w] for w in set(re.findall(r"\w{5,}", x.lower()))) / (len(x) ** 0.5)
                    + (3 if re.search(r"\d", x) else 0) + (4 if i < 2 else 0))
        keep = sorted(sorted(range(len(sents)), key=lambda i: -sc(i))[:n])
        sents = [sents[i] for i in keep]
    if not sents:
        return ""
    if lang != source_lang:
        joined = _free_chunk("\n".join(sents), lang)
        parts = [x.strip() for x in joined.split("\n") if x.strip()]
        if len(parts) == len(sents):
            sents = parts
    return "\n".join("- " + x for x in sents)
