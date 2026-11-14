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
    if lang == "sr":  # žargon u običan engleski pre prevoda, da prevod ne bude doslovan
        import translate_fix
        texts = [translate_fix.simplify_en(x) for x in texts]
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
    if lang == "sr":
        import translate_fix
        result = [translate_fix.polish_sr(x) if x else x for x in result]
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
              "Na osnovu naslova i kratkog opisa (pun tekst nije dostupan) izdvoji suštinu u 3-5 jasnih rečenica: "
              "šta se desilo, koji su najvažniji nalazi i konkretne brojke/vremenski okvir ako su navedeni, "
              "i zašto bi to moglo biti važno za investitore. Razdvoji potvrđenu činjenicu od mogućeg tumačenja. "
              "Ne izmišljaj brojke, uzroke ili reakciju tržišta; ako je opis prekratak, jasno reci šta nedostaje.\n\n"
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
    """Sažima pojedinačnu vest: suština, proverljive činjenice i važne brojke."""
    if llm_on():
        prompt = (f"Odgovori na: {_lang_instr(lang)}\n"
                  "Sažmi članak u 4-6 kratkih markdown tačaka. Prva tačka treba da kaže suštinu. "
                  "Izdvoji šta se dogodilo ili šta je zaključeno, konkretne nalaze i sve važne brojke "
                  "(iznose, procente, period, uzorak, poređenja i jedinice) tačno kako su navedeni. "
                  "Ne izostavljaj brojke koje menjaju značenje vesti. Zatim dodaj pasus „Zašto je bitno:“ "
                  "i poveži ga sa tržištem samo kada tekst za to daje osnov. Razdvoji činjenice od tumačenja. "
                  "Ne nagađaj i ne izmišljaj podatke; ako su dostupni samo naslov/opis ili je dokaz nepotpun, "
                  "jasno navedi ograničenje.\n\n"
                  f"NASLOV: {title}\n\nTEKST:\n{text[:14000]}")
        return _claude(prompt, FAST_MODEL, 1000)
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
    import translate_fix
    src = translate_fix.simplify_en(chunk) if lang == "sr" else chunk
    try:
        out = gtx(src, lang)
    except Exception as ex:  # noqa: BLE001
        LAST_ERROR = str(ex)[:200]
        out = _fallback_one(src, lang)
    return translate_fix.polish_sr(out) if lang == "sr" and out else out


def analyze_paper(title, abstract, conclusion, lang, thesis=""):
    """Strukturisana analiza rada za istraživača (zahteva API ključ)."""
    prompt = (f"Odgovori na: {_lang_instr(lang)}\n"
              "Ti si mentor na doktorskim studijama iz finansijskog inženjerstva i računarske inteligencije. "
              "Analiziraj rad u kratkim markdown tačkama sa podnaslovima: **Suština**, **Problem**, **Metod**, "
              "**Podaci**, **Glavni nalazi i brojke**, **Ograničenja**, **Kako se nadovezuje na moj master rad** "
              "(konkretno, 1-3 tačke), **Ideja za doktorat** (1-2 konkretna pravca). U glavnim nalazima sačuvaj "
              "tačne rezultate, veličinu uzorka, periode, procente, p-vrednosti, intervale i poređenja kada postoje. "
              "Koristi samo informacije iz abstracta i zaključka; ne zaključuj brojke koje nisu navedene. Ako podatak "
              "nedostaje, označi ga kao nedostupan.\n\n"
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
    if has_key() or ollama_on():
        out = {}
        for k in range(0, len(papers), 10):
            chunk = papers[k:k + 10]
            data = [{"id": p["id"], "title": p["title"], "text": ((p.get("abstract") or "") + " " + (p.get("conclusion") or ""))[:2500]}
                    for p in chunk]
            prompt = (f"Za svaku studiju napiši KLJUČNI NALAZ na jeziku: {_lang_instr(lang)} "
                      "U 1-3 kratke rečenice izdvoji suštinu i konkretan rezultat. Sačuvaj tačne brojke ako postoje: "
                      "veličinu uzorka, procente, veličinu efekta, interval pouzdanosti, p-vrednost, period i poređenje "
                      "sa baznom metodom. Navedi metod/podatke samo ako su dati u tekstu. Bez uvoda tipa "
                      "'Studija istražuje'. Ako nema brojčanog rezultata, nemoj ga izmišljati. Vrati SAMO JSON listu "
                      "objekata {\"id\": ..., \"f\": ...}.\n\n" + json.dumps(data, ensure_ascii=False))
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



def local_news_summary(period_label, items, lang):
    """Create a filter-aware news summary using only the configured local Ollama model."""
    if not ollama_on():
        raise RuntimeError("Ollama local model is not available.")
    rows = []
    for i, item in enumerate(items[:60], 1):
        rows.append(
            f"{i}. [{item.get('source') or '-'} | {item.get('category') or '-'}] "
            f"{item.get('title') or '-'}\n"
            f"   Description: {(item.get('summary') or '-')[:700]}\n"
            f"   Link: {item.get('link') or '-'}"
        )
    if lang == "sr":
        prompt = (
            f"Napiši sažetak finansijskih vesti za period {period_label}, na "
            f"{_lang_instr('sr')}.\n"
            "Sažetak zasnuj isključivo na priloženim naslovima i opisima. Grupiši iste događaje i izdvoji "
            "suštinu i 4-7 najvažnijih nalaza. Sačuvaj sve relevantne brojke tačno (iznose, procente, rokove, "
            "promene i vremenski period) i navedi na koju kompaniju, tržište ili meru se odnose. Objasni šta se "
            "promenilo i šta treba pratiti. Ne izmišljaj brojke, uzroke, reakcije tržišta ni zaključke kojih nema "
            "u izvorima. Razdvoji potvrđene informacije od neizvesnosti i dodaj link uz svaku tvrdnju. Ako su opisi "
            "kratki ili nepotpuni, jasno reci.\n"
            "Koristi naslove: Ukratko, Najvažniji nalazi i brojke, Šta pratiti.\n\nVESTI:\n"
        )
    else:
        prompt = (
            f"Write a financial news summary for {period_label} in {_lang_instr('en')}.\n"
            "Use only the supplied headlines and descriptions. Merge duplicate events and identify "
            "the essence and 4-7 key findings. Preserve each relevant figure exactly (amounts, percentages, "
            "dates, changes and time periods), naming the company, market or measure it refers to. Explain "
            "what changed and what to watch. Do not invent figures, causes, market reactions or conclusions. "
            "Separate reported facts from uncertainty, link every claim to its source, and state when "
            "descriptions are incomplete. Use headings: In short, Key findings and figures, What to watch.\n\nNEWS:\n"
        )
    return _ollama(prompt + "\n".join(rows), max_tokens=2200)


def local_research_summary(topic_label, period_label, papers, lang):
    """Synthesize selected papers and available conclusions using only local Ollama."""
    if not ollama_on():
        raise RuntimeError("Ollama local model is not available.")
    rows = []
    for i, paper in enumerate(papers[:30], 1):
        conclusion = (paper.get("conclusion") or "").strip()
        finding = (paper.get("finding") or "").strip()
        abstract = (paper.get("abstract") or "").strip()
        evidence = conclusion or finding or abstract or "No conclusion or abstract available."
        evidence_kind = "Conclusion" if conclusion else ("Extracted finding" if finding else "Abstract")
        rows.append(
            f"{i}. {paper.get('title') or '-'} | {paper.get('venue') or '-'} | "
            f"{paper.get('pub_date') or '-'} | citations: {paper.get('cited_by') or 0}\n"
            f"   Evidence ({evidence_kind}): {evidence[:1800]}\n"
            f"   Source: {paper.get('link') or '-'}"
        )
    if lang == "sr":
        prompt = (
            f"Napravi sažetak istraživanja za temu „{topic_label}“ i period {period_label}, "
            f"na {_lang_instr('sr')}. Rangirani radovi ispod odgovaraju već izabranom periodu i filterima.\n"
            "Prvo koristi zaključak kada postoji, zatim izdvojeni nalaz, pa abstract. Izdvoji suštinu i "
            "nalaze najvažnijih studija; sačuvaj tačne brojke kao što su uzorak, procenat, veličina efekta, "
            "p-vrednost, interval pouzdanosti, vremenski period i poređenje, ako su navedeni. Uporedi gde se "
            "rezultati slažu ili razlikuju, a metode/podatke navedi samo ako su prikazani. Osloni se isključivo "
            "na sadržaj radova, bez izmišljanja, i poveži svaku tvrdnju sa konkretnim radom. Ako je dostupan samo "
            "abstract ili kratak nalaz, jasno naznači ograničenje.\n"
            "Koristi naslove: Suština i glavni nalazi, Najvažnije brojke, Gde se studije slažu ili razlikuju, "
            "Metode, ograničenja i otvorena pitanja.\n\nSTUDIJE:\n"
        )
    else:
        prompt = (
            f"Summarize research on “{topic_label}” for {period_label} in {_lang_instr('en')}. "
            "The papers below already match the selected period and filters.\n"
            "Prefer each paper's conclusion, then its extracted finding, then its abstract. Summarize "
            "the essence and findings of the most important studies. Preserve exact sample sizes, percentages, "
            "effect sizes, p-values, confidence intervals, time periods and comparisons when supplied. Compare "
            "agreement and disagreement, and report methods/data only when stated. Use only the papers, invent "
            "nothing, link every claim to a paper, and say when evidence is only an abstract or short finding. "
            "Use headings: Essence and main findings, Key figures, Agreement and disagreement, Methods, "
            "limitations and open questions.\n\nPAPERS:\n"
        )
    return _ollama(prompt + "\n".join(rows), max_tokens=2600)


def quick_summary(text, lang, source_lang="en", n=5):
    """Suština vesti sa najvažnijim činjenicama i brojkama; ekstraktivni rezervni režim."""
    flat = re.sub(r"\s+", " ", text or "").strip()
    if llm_on() and flat:
        prompt = (f"Odgovori na: {_lang_instr(lang)}\n"
                  "Sažmi ovu vest u 4-6 kratkih tačaka. Prva tačka treba da izvuče suštinu. "
                  "Sačuvaj konkretne nalaze i važne brojke tačno kako su navedeni: iznos, procenat, "
                  "datum/period, promenu, poređenje i na koga se odnose. Objasni značaj samo ako ga "
                  "tekst podržava. Ne izmišljaj brojke ili uzroke; ako vest ne daje dovoljno podataka, "
                  "navedi šta nedostaje. Vrati samo kratku markdown listu, bez uvoda.\n\n"
                  f"TEKST VESTI:\n{flat[:11000]}")
        try:
            summary = _claude(prompt, FAST_MODEL, 850)
            if summary:
                return summary
        except Exception:  # noqa: BLE001
            pass
    sents = [x for x in re.split(r"(?<=[.!?])\s+", flat) if 40 <= len(x) <= 420]
    if len(sents) > n:
        words = Counter(w for w in re.findall(r"\w{5,}", flat.lower()))
        def sc(i):
            x = sents[i]
            numeric = len(re.findall(r"\d+(?:[.,]\d+)?\s*%?|[$€£]|\b(?:million|billion|trillion|miliona|milijarde)\b", x, re.I))
            cues = sum(k in x.lower() for k in ("reported", "announced", "rose", "fell", "expects", "forecast", "found", "results", "earnings", "revenue", "reported", "iznos", "porast", "pad", "rezultat"))
            return (sum(words[w] for w in set(re.findall(r"\w{5,}", x.lower()))) / (len(x) ** 0.5)
                    + min(5, numeric) * 1.3 + cues * 1.2 + (2 if i < 2 else 0))
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