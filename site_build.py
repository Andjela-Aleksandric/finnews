"""FinNews sajt: osvežava podatke i pravi JSON fajlove koje čita veb aplikacija (GitHub Pages).

Pokreće ga GitHub Action na svakih 30 minuta:
  python site_build.py                -> preuzmi vesti/cene/radove, prevedi, izvezi u web/public/data
  python site_build.py --export-only  -> samo izvoz iz postojeće baze (za proveru)

Javni podaci (vesti, akcije, cene, radovi) idu na sajt. Celi tekstovi vesti i portfolio idu SAMO u
privatni repozitorijum (FINNEWS_REPO), jer su lični ili pripadaju redakcijama."""
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import ai
import db
import eu
import fetcher
import reader
import signals
import stocks

OUT = Path(os.environ.get("OUT", Path(__file__).parent / "web" / "public" / "data"))
RESEARCH = "Istraživanja"
SECTIONS = {"fin": ["Vesti", "Centralne banke i makro", "Analize i blogovi", "Srbija i region"], "comp": ["Kompanije"],
            "srb": ["Srbija", "Srbija i region"], "svet": ["Svet"]}
SECTIONS["all"] = SECTIONS["fin"] + ["Kompanije", "Srbija", "Svet"]
PERIODS = [1, 7, 30, 60, 90, 180]
RESEARCH_PERIODS = (7, 30, 60, 180)  # filter i AI pregled istraživanja


def _cap(x):
    x = (x or "").strip()
    return x[:1].upper() + x[1:]

THEMES = [("Fed", "Fed", r"\bfed\b|federal reserve|fomc|powell"), ("ECB", "ECB", r"\becb\b|lagarde|eurozone|euro zone"),
          ("Inflacija", "Inflation", r"inflation|\bcpi\b|\bpce\b|inflacij"),
          ("Kamate i obveznice", "Rates & bonds", r"rate cut|rate hike|interest rate|yield|treasur|bond|kamat"),
          ("Tržište rada", "Labour market", r"\bjobs\b|payroll|unemployment|labor market"),
          ("Rezultati kompanija", "Earnings", r"earnings|guidance|profit|revenue"),
          ("Tehnologija i AI", "Tech & AI", r"nvidia|\bai\b|artificial intelligence|chip|semiconductor|apple|microsoft|alphabet|meta\b"),
          ("Nafta i energija", "Oil & energy", r"\boil\b|opec|crude|natural gas|energy"), ("Zlato", "Gold", r"\bgold\b"),
          ("Kripto", "Crypto", r"bitcoin|crypto|stablecoin|ether"), ("Carine i trgovina", "Tariffs & trade", r"tariff|trade war|sanction|export"),
          ("Kina", "China", r"china|chinese|beijing|pboc"), ("Srbija", "Serbia", r"\bnbs\b|srbij|serbia|belex|dinar")]
WTHEMES = [("Politika", "Politics", r"vlad|izbor|skupštin|predsednik|premijer|ministar|stranka|government|election|parliament|president|minister|party"),
           ("Ekonomija", "Economy", r"ekonom|inflac|plat|penzij|cen[ae]|budžet|investic|econom|inflation|wage|price|budget|gdp|tariff"),
           ("Rat i bezbednost", "War & security", r"\brat\b|rata|napad|vojsk|oružj|\bwar\b|attack|military|ceasefire|missile|troops|drone"),
           ("EU i diplomatija", "EU & diplomacy", r"\beu\b|evrop|diplomat|samit|nato|ambasad|europe|summit|diplomac|embassy"),
           ("Društvo", "Society", r"škol|zdrav|bolnic|protest|student|obrazov|health|school|hospital|protest|education"),
           ("Tehnologija", "Technology", r"\bai\b|veštačk|tehnolog|tech|artificial intelligence|chip|startup"),
           ("Nesreće i klima", "Disasters & climate", r"zemljotres|poplav|požar|klim|nesreć|earthquake|flood|wildfire|climate|storm")]
SEC_THEMES = {"fin": THEMES, "comp": THEMES, "srb": WTHEMES, "svet": WTHEMES, "all": THEMES + WTHEMES}


def log(*a):
    print(datetime.now().strftime("%H:%M:%S"), *a, flush=True)


def iso(dt):
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


def now():
    return datetime.now(timezone.utc)


def _polish_all(obj):
    """Završna provera svakog srpskog teksta pre objave: doslovni idiomi ("vruća inflacija"), ";" i hrvatske reči."""
    import translate_fix
    if isinstance(obj, str):
        return translate_fix.polish_sr(obj) if " " in obj and not obj.startswith("http") else obj
    if isinstance(obj, list):
        return [_polish_all(x) for x in obj]
    if isinstance(obj, dict):
        return {k: (v if k in ("en", "t", "u", "id", "s", "link", "url") and isinstance(v, str) else _polish_all(v)) for k, v in obj.items()}
    return obj


def dump(name, obj):
    obj = _polish_all(obj)
    p = OUT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return p.stat().st_size


def dedupe(items, limit):
    kept, extra, toks = [], {}, []
    for it in items:
        tk = fetcher.tokens(it["title"])
        dup = None
        for i, k in enumerate(toks):
            inter = len(tk & k)
            if tk and inter >= 3 and inter / len(tk | k) >= 0.3:
                dup = i
                break
        if dup is None:
            kept.append(it); toks.append(tk)
        else:
            extra[kept[dup]["id"]] = extra.get(kept[dup]["id"], 0) + 1
        if len(kept) >= limit:
            break
    return kept, extra


# ---------- osvežavanje ----------
def pretranslate(con, lang, hours=72, limit=600, days=190, max_items=5000, budget=540):
    """Prevodi SVE vesti iz poslednjih `days` dana koje nemaju prevod (najnovije prvo), ponavlja prevode koji su ostali
    na engleskom i, kad se promene pravila prevoda, ponovo prevodi najvažnije vesti iz poslednja 3 dana."""
    import time as _time
    import translate_fix
    t0 = _time.time()
    pool = db.query_items(con, start_iso=iso(now() - timedelta(days=days)), order="time", limit=40000)
    pool = [i for i in pool if (i.get("lang") or "en") != lang]
    have = db.get_translations(con, [i["id"] for i in pool], lang)
    vkey = f"tr_version_{lang}"
    redo_v = lang == "sr" and (db.get_meta(con, vkey) or "") != translate_fix.TR_VERSION
    week = iso(now() - timedelta(days=7))
    # nova pravila prevoda: ponovo se prevode sve vesti iz poslednjih 7 dana (u više osvežavanja ako ih je mnogo)
    done_key = f"tr_redo_done_{lang}_{translate_fix.TR_VERSION}"
    done = set(json.loads(db.get_meta(con, done_key) or "[]")) if redo_v else set()
    top = {i["id"] for i in pool if i["published"] >= week and i["id"] not in done} if redo_v else set()
    bad = set()
    if lang == "sr":  # sačuvani "prevodi" koji su ostali na engleskom (naslov ili opis), za poslednjih 7 dana
        bad = {i["id"] for i in pool if i["id"] in have and i["published"] >= week
               and (translate_fix.looks_english(have[i["id"]]["title"]) or have[i["id"]]["title"] == i["title"]
                    or translate_fix.looks_english((have[i["id"]].get("summary") or "")[:300]))}
        if bad:
            log(f"prevodi koji su ostali na engleskom: {len(bad)}, npr. {[have[b]['title'] for b in list(bad)[:3]]}")
    missing = [i for i in pool if i["id"] not in have]
    log(f"prevod {lang}: bez prevoda {len(missing)} od {len(pool)} vesti ({days} dana)")
    # redosled: poslednja 3 dana bez prevoda, zatim loši prevodi, pa nova pravila, pa ostatak nedelje i meseca
    recent = iso(now() - timedelta(hours=hours))
    seen, todo = set(), []
    for group in ([i for i in missing if i["published"] >= recent], [i for i in pool if i["id"] in bad],
                  [i for i in pool if i["id"] in top], missing):
        for i in group:
            if i["id"] not in seen:
                seen.add(i["id"]); todo.append(i)
    full = len(todo) <= max_items
    todo = todo[:max_items]
    ok, finished = 0, True
    for k in range(0, len(todo), 60):
        if _time.time() - t0 > budget:
            log(f"prevod {lang}: vreme isteklo posle {k} vesti, ostatak u sledećem osvežavanju")
            finished = False
            break
        chunk = todo[k:k + 60]
        for it, (tt, ss) in zip(chunk, ai.translate_items([(i["title"], (i.get("summary") or "")[:450]) for i in chunk], lang)):
            if tt and tt != it["title"] and not (lang == "sr" and translate_fix.looks_english(tt)):
                db.save_translation(con, it["id"], lang, tt, ss)
                ok += 1
                if it["id"] in top:
                    done.add(it["id"])
    if redo_v:
        db.set_meta(con, done_key, json.dumps(sorted(done)))
    redo = redo_v and finished and full
    log(f"prevod {lang}: {ok}/{len(todo)}" + (f" ({ai.LAST_ERROR})" if ai.LAST_ERROR else ""))
    if redo and ok:
        db.set_meta(con, vkey, translate_fix.TR_VERSION)
    if lang == "sr":  # dijagnostika: srpski naslovi i opisi u kojima su ostale engleske reči
        try:
            recent = db.query_items(con, start_iso=iso(now() - timedelta(hours=168)), order="time", limit=40000)
            tr = db.get_translations(con, [i["id"] for i in recent], lang)
            log(f"prevod sr - posle osvežavanja bez prevoda: {sum(1 for i in recent if i['id'] not in tr and (i.get('lang') or 'en') != lang)} od {len(recent)} (7 dana)")
            mixed = []
            for i in recent:
                t = tr.get(i["id"])
                if not t or (i.get("lang") or "en") == lang:
                    continue
                for part in ("title", "summary"):
                    w = translate_fix.english_words(t.get(part) or "")
                    if w:
                        mixed.append((part, w, (t.get(part) or "")[:160]))
            log(f"prevod sr - mešani tekstovi: {len(mixed)} od {len(recent)}")
            for m in mixed[:8]:
                log("   ", m)
        except Exception as ex:  # noqa: BLE001
            log("! dijagnostika prevoda:", ex)


def refresh(con):
    import run_fetch
    cfg = ai.load_config()
    cfg["ui_lang"] = "sr"
    cfg.setdefault("auto_read", True)
    ai.save_config(cfg)
    run_fetch.run(con, log=lambda *a: log(*a))
    try:  # obične engleske reči iz vesti - da naslovi Svakom Reči Velikim Slovom ne bi delovali kao imena
        import translate_fix
        its = db.query_items(con, start_iso=iso(now() - timedelta(days=10)), limit=3000)
        log(f"rečnik za prevod: {translate_fix.load_vocab([i.get('summary') or '' for i in its])} reči")
    except Exception as ex:  # noqa: BLE001
        log(f"rečnik za prevod nije učitan: {ex}")
    pretranslate(con, "sr")
    pretranslate(con, "en")
    try:
        build_briefs(con)
    except Exception as ex:  # noqa: BLE001
        log("! sažeci vesti:", ex)
    try:
        run_local_ai(con)
        build_briefs(con)  # prevod novih AI sažetaka na srpski
    except Exception as ex:  # noqa: BLE001
        log("! lokalni AI:", ex)
    try:
        retranslate_findings(con)
    except Exception as ex:  # noqa: BLE001
        log("! prevod nalaza:", ex)
    # trenutni sažeci i na engleskom za najvažnije vesti
    for it in sorted(db.query_items(con, start_iso=iso(now() - timedelta(hours=36)), exclude_categories=[RESEARCH], limit=300),
                     key=lambda x: -fetcher.relevance(x))[:60]:
        a = db.get_article(con, it["id"])
        if a and reader.is_full(a["status"]) and not db.get_article_ai(con, it["id"], "en", "quick"):
            q = ai.quick_summary(a["text"], "en", it.get("lang") or "en")
            if q:
                db.save_article_ai(con, it["id"], "en", "quick", q)
    # ceo prevod na srpski za najčitanije (keširano)
    n = 0
    for it in sorted(db.query_items(con, start_iso=iso(now() - timedelta(hours=48)), exclude_categories=[RESEARCH], limit=300),
                     key=lambda x: -fetcher.relevance(x))[:60]:
        if n >= 25 or (it.get("lang") or "en") == "sr":
            continue
        a = db.get_article(con, it["id"])
        if a and reader.is_full(a["status"]) and not db.get_article_ai(con, it["id"], "sr", "full"):
            tr = ai.translate_full(a["text"], "sr")
            if tr and tr[:80] != a["text"][:80]:
                db.save_article_ai(con, it["id"], "sr", "full", tr)
                n += 1
    log(f"celi prevodi: {n}")


# ---------- izvoz ----------
def tr_map(con, ids):
    out = {}
    for lang in ("sr", "en"):
        for k, v in db.get_translations(con, ids, lang).items():
            t, sm = v["title"], (v.get("summary") or "")[:450]
            if lang == "sr":  # i starije, već sačuvane prevode očisti od doslovnih izraza
                import translate_fix
                t, sm = translate_fix.polish_sr(t), translate_fix.polish_sr(sm)
            out.setdefault(k, {})[lang] = [t, sm]
    return out


def full_ids(con, ids):
    return {k for k, v in reader.statuses(con, ids).items() if reader.is_full(v)}


def build_briefs(con, hours=72, limit=500):
    """Za svaku vest sa celim tekstom: sažetak od 2-3 rečenice iz teksta (engleski i srpski), keširano."""
    import translate_fix
    if db.get_meta(con, "brief_tr_version") != translate_fix.TR_VERSION:  # nova pravila prevoda - srpski sažeci se prevode ponovo
        con.execute("DELETE FROM article_ai WHERE kind='brief' AND lang='sr' AND EXISTS "
                    "(SELECT 1 FROM article_ai e WHERE e.item_id=article_ai.item_id AND e.kind='brief' AND e.lang='en')")
        con.commit()
        db.set_meta(con, "brief_tr_version", translate_fix.TR_VERSION)
    items = db.query_items(con, start_iso=iso(now() - timedelta(hours=hours)), exclude_categories=[RESEARCH], limit=limit)
    made = 0
    for it in items:
        if db.get_article_ai(con, it["id"], "en", "brief") or db.get_article_ai(con, it["id"], "sr", "brief"):
            continue
        a = db.get_article(con, it["id"])
        if not a or not reader.is_full(a["status"]):
            continue
        b = ai.brief_sentences(a["text"])
        if len(b) < 120:
            continue
        db.save_article_ai(con, it["id"], "sr" if (it.get("lang") or "en") == "sr" else "en", "brief", b)
        made += 1
    # prevod sažetaka koji nedostaju (imena ljudi ostaju u originalu)
    for src, dst in (("en", "sr"), ("sr", "en")):
        rows = con.execute("SELECT a.item_id, a.content FROM article_ai a WHERE a.kind='brief' AND a.lang=? AND NOT EXISTS "
                           "(SELECT 1 FROM article_ai b WHERE b.item_id=a.item_id AND b.kind='brief' AND b.lang=?) LIMIT 400",
                           (src, dst)).fetchall()
        for k in range(0, len(rows), 40):
            chunk = rows[k:k + 40]
            try:
                out = ai._free_translate([(r["content"], "") for r in chunk], dst)
            except Exception:  # noqa: BLE001
                break
            for r, (tr, _) in zip(chunk, out):
                if tr and tr != r["content"]:
                    db.save_article_ai(con, r["item_id"], dst, "brief", tr)
    log(f"sažeci vesti (2-3 rečenice): {made} novih")


def brief_map(con, ids):
    out = {}
    ids = list(ids)
    for k in range(0, len(ids), 800):
        part = ids[k:k + 800]
        q = "SELECT item_id, lang, content FROM article_ai WHERE kind='brief' AND item_id IN (%s)" % ",".join("?" * len(part))
        for r in con.execute(q, part):
            out.setdefault(r["item_id"], {})[r["lang"]] = r["content"]
    return out


def run_local_ai(con):
    """Besplatan lokalni AI: pregledi perioda po sekcijama, sažeci vesti i nalazi studija (u vremenskom budžetu)."""
    import hashlib
    import local_ai
    if not local_ai.available():
        log("lokalni AI: model nije dostupan - preskačem")
        return
    local_ai.start_budget(int(os.environ.get("LOCAL_AI_BUDGET", "720")))
    stats = {"pregledi": 0, "vesti": 0, "studije": 0}
    t0 = now()
    rows = db.query_items(con, start_iso=iso(t0 - timedelta(days=31)), exclude_categories=[RESEARCH], order="date", limit=20000)
    briefs = brief_map(con, [r["id"] for r in rows])
    max_age = {1: 2, 7: 6, 30: 24}
    # 1) pregledi perioda za sekcije (najvredniji deo, idu prvi)
    for p in (1, 7, 30):
        for sec, cats in SECTIONS.items():
            if local_ai.time_left() < 60:
                continue
            a = iso(t0 - timedelta(days=p))
            pool = sorted([r for r in rows if r["category"] in cats and r["published"] >= a], key=lambda x: -(x["score"] or 0))
            top, _ = dedupe(pool, 8)
            if len(top) < 3:
                continue
            h = hashlib.md5(("v2|" + "|".join(x["id"] for x in top)).encode()).hexdigest()[:12]
            key = f"ai_digest_{sec}_{p}"
            try:
                old = json.loads(db.get_meta(con, key) or "{}")
            except ValueError:
                old = {}
            stale = old.get("en") and not all(local_ai.good_point(x) and not re.match(r"\s*\d+[.)]\s", x) for x in old["en"])
            if not stale and (old.get("h") == h or (old.get("at") and now() - datetime.fromisoformat(old["at"]) < timedelta(hours=max_age[p]))):
                continue
            items = [{"title": x["title"], "text": (briefs.get(x["id"], {}).get("en") or x.get("summary") or "")} for x in top]
            try:
                pts = local_ai.digest(f"the last {p} day" + ("s" if p > 1 else ""), items)
            except Exception as ex:  # noqa: BLE001
                log("! lokalni AI pregled:", ex)
                continue
            if not pts:
                continue
            sr = [_cap(t) for t, _ in ai._free_translate([(x, "") for x in pts], "sr")]
            db.set_meta(con, key, json.dumps({"h": h, "at": iso(now()), "ids": [x["id"] for x in top], "en": pts, "sr": sr, "v": __import__("translate_fix").TR_VERSION}, ensure_ascii=False))
            if not stats["pregledi"]:
                log(f"  primer AI pregleda ({sec}, {p} d): {sr[:2]}")
            stats["pregledi"] += 1
    # 1a) pregled vesti po kompaniji (7 dana), prikazan na profilu akcije i u portfoliju
    stats["pregledi_kompanija"] = 0
    by_ticker = {}
    cutoff = iso(t0 - timedelta(days=7))
    for row in rows:
        # DB redovi koriste kolonu `ticker`. `tk` se dodaje tek pri izvozu u JSON.
        ticker = (row.get("ticker") or "").strip().upper()
        if ticker and row.get("published", "") >= cutoff:
            by_ticker.setdefault(ticker, []).append(row)
    # Nedostajuće preglede obrađujemo prve. Pozicije koje se često koriste na
    # evropskim berzama imaju prednost, jer se njihovi tickers razlikuju od
    # američkih simbola za istu kompaniju (npr. ABEA.DE i GOOGL).
    company_priority = {ticker: i for i, (ticker, _name) in enumerate(eu.EU_WATCHLIST)}
    company_groups = []
    for ticker, pool in by_ticker.items():
        try:
            old = json.loads(db.get_meta(con, f"ai_company_news_7d_{ticker}") or "{}")
        except ValueError:
            old = {}
        company_groups.append((ticker, pool, old))
    company_groups.sort(key=lambda entry: (bool(entry[2].get("en")), company_priority.get(entry[0], len(company_priority)),
                                           entry[2].get("at") or "", -len(entry[1]), entry[0]))
    company_attempts = 0
    for ticker, pool, old in company_groups:
        if local_ai.time_left() < 100 or company_attempts >= 20:
            break
        top, _ = dedupe(sorted(pool, key=lambda x: (x.get("published") or "", x.get("score") or 0), reverse=True), 8)
        if not top:
            continue
        ids = [x["id"] for x in top]
        h = hashlib.md5(("company-news-7d-v1|" + "|".join(ids)).encode()).hexdigest()[:12]
        key = f"ai_company_news_7d_{ticker}"
        if old.get("h") == h:
            continue
        company_attempts += 1
        digest_items = [{"title": x["title"], "text": briefs.get(x["id"], {}).get("en") or x.get("summary") or ""} for x in top]
        try:
            pts = local_ai.digest("the last 7 days for " + ticker, digest_items)
        except Exception as ex:  # noqa: BLE001
            log("! AI pregled vesti kompanije:", ticker, ex)
            continue
        if not pts:
            continue
        # Čuvamo reference i posle prevoda da svaka tačka može da otvori izvorne vesti.
        plain = [re.sub(r"\s*(?:\[\d+\])+\s*\.?$", "", point).strip() for point in pts]
        refs = ["".join(re.findall(r"\[\d+\]", point)) for point in pts]
        translated = ai._free_translate([(point, "") for point in plain], "sr")
        sr = [_cap((translated[i][0] if i < len(translated) else "") or plain[i]) + (" " + refs[i] if refs[i] else "") for i in range(len(plain))]
        db.set_meta(con, key, json.dumps({"h": h, "at": iso(now()), "days": 7, "ids": ids, "count": len(top), "en": pts, "sr": sr,
                                          "v": __import__("translate_fix").TR_VERSION}, ensure_ascii=False))
        stats["pregledi_kompanija"] += 1
    # 1a) pregled za investitora (stanje tržišta, rizici, prilike, šta pratiti) za 1 i 7 dana, iz finansija i kompanija
    stats["strategija"] = 0
    for p, age in ((1, 3), (7, 12)):
        if local_ai.time_left() < 120:
            break
        a = iso(t0 - timedelta(days=p))
        pool = sorted([r for r in rows if r["category"] in SECTIONS["fin"] + SECTIONS["comp"] and r["published"] >= a], key=lambda x: -(x["score"] or 0))
        top, _ = dedupe(pool, 10)
        if len(top) < 4:
            continue
        h = hashlib.md5(("s1|" + "|".join(x["id"] for x in top)).encode()).hexdigest()[:12]
        key = f"ai_strategy_{p}"
        try:
            old = json.loads(db.get_meta(con, key) or "{}")
        except ValueError:
            old = {}
        if old.get("h") == h or (old.get("at") and now() - datetime.fromisoformat(old["at"]) < timedelta(hours=age)):
            continue
        items = [{"title": x["title"], "text": (briefs.get(x["id"], {}).get("en") or x.get("summary") or "")} for x in top]
        try:
            st = local_ai.strategist(f"the last {p} day" + ("s" if p > 1 else ""), items)
        except Exception as ex:  # noqa: BLE001
            log("! lokalni AI strategija:", ex)
            continue
        if not st:
            continue
        flat = [(k, x) for k in local_ai.STRATEGY_KEYS for x in st.get(k, [])]
        srt = [_cap(t) for t, _ in ai._free_translate([(x, "") for _, x in flat], "sr")]
        sr = {}
        for (k, _), t in zip(flat, srt):
            sr.setdefault(k, []).append(t)
        db.set_meta(con, key, json.dumps({"h": h, "at": iso(now()), "ids": [x["id"] for x in top], "en": st, "sr": sr, "model": local_ai.MODEL}, ensure_ascii=False))
        stats["strategija"] += 1
        log(f"  AI pregled za investitora ({p} d): {srt[:2]}")
    try:
        papers = [p for p in db.phd_papers(con, limit=800) if (p.get("abstract") or "")]
    except Exception:  # noqa: BLE001
        papers = []
    # 1b) pregled istraživanja za 7, 30, 60 i 180 dana (iz nalaza najznačajnijih studija)
    stats["istraživanja"] = 0
    for p in RESEARCH_PERIODS:
        if local_ai.time_left() < 60:
            break
        since = (date.today() - timedelta(days=p)).isoformat()
        sel = [x for x in papers if (x.get("pub_date") or "") >= since]
        sel = [dict(x, text=(db.get_article_ai(con, x["id"], "en", "finding4") or "").split("\n\n")[0]) for x in sel]
        sel = [x for x in sel if x["text"]][:10]
        log(f"pregled istraživanja {p} dana: {len(sel)} studija sa nalazom")
        if len(sel) < (2 if p <= 7 else 3):
            continue
        h = hashlib.md5(("v3|" + "|".join(x["id"] for x in sel)).encode()).hexdigest()[:12]
        key = f"ai_rdigest_{p}"
        try:
            old = json.loads(db.get_meta(con, key) or "{}")
        except ValueError:
            old = {}
        if old.get("h") == h:
            continue
        try:
            pts = local_ai.research_digest(f"the last {p} days", sel)
        except Exception as ex:  # noqa: BLE001
            log("! lokalni AI istraživanja:", ex)
            break
        if pts:
            sr = [_cap(t) for t, _ in ai._free_translate([(x, "") for x in pts], "sr")]
            db.set_meta(con, key, json.dumps({"h": h, "at": iso(now()), "ids": [x["id"] for x in sel], "en": pts, "sr": sr, "v": __import__("translate_fix").TR_VERSION}, ensure_ascii=False))
            stats["istraživanja"] += 1
    # 2) sažeci vesti sa celim tekstom (zamenjuju izvučene rečenice)
    cand = sorted([r for r in rows if r["published"] >= iso(t0 - timedelta(hours=48))], key=lambda x: -fetcher.relevance(x))[:200]
    for it in cand:
        if local_ai.time_left() < 150:
            break
        if db.get_article_ai(con, it["id"], "en", "brief_ai") or (it.get("lang") or "en") == "sr":
            continue
        a = db.get_article(con, it["id"])
        if not a or not reader.is_full(a["status"]):
            continue
        try:
            b = local_ai.news_brief(it["title"], a["text"])
        except Exception as ex:  # noqa: BLE001
            log("! lokalni AI vest:", ex)
            break
        db.save_article_ai(con, it["id"], "en", "brief_ai", b or "-")
        if b:
            db.save_article_ai(con, it["id"], "en", "brief", b)
            con.execute("DELETE FROM article_ai WHERE item_id=? AND kind='brief' AND lang='sr'", (it["id"],))
            con.commit()
            if not stats["vesti"]:
                log(f"  primer AI sažetka: {it['title'][:80]} -> {b[:300]}")
            stats["vesti"] += 1
    # 3) nalazi studija (rezultat + ključni doprinos)
    try:
        papers = [p for p in db.phd_papers(con, limit=800) if (p.get("abstract") or "")]
    except Exception:  # noqa: BLE001
        papers = []
    for p in papers:
        if local_ai.time_left() < 60:
            break
        if db.get_article_ai(con, p["id"], "en", "finding_ai"):
            continue
        art = db.get_article(con, p["id"])
        concl = art["text"] if art and art["status"] == "concl" else ""
        try:
            res, contrib = local_ai.paper_finding(p["title"], p.get("abstract"), concl)
        except Exception as ex:  # noqa: BLE001
            log("! lokalni AI studija:", ex)
            break
        db.save_article_ai(con, p["id"], "en", "finding_ai", "1")
        if not res:
            continue
        (rs, cs), = ai._free_translate([(res, contrib)], "sr")
        db.save_article_ai(con, p["id"], "en", "finding4", res + (f"\n\nKey contribution: {contrib}" if contrib else ""))
        db.save_article_ai(con, p["id"], "sr", "finding4", (rs or res) + (f"\n\nKljučni doprinos: {cs or contrib}" if contrib else ""))
        if not stats["studije"]:
            log(f"  primer AI nalaza: {(rs or res)[:220]} | {(cs or contrib)[:160]}")
        stats["studije"] += 1
    log(f"lokalni AI ({local_ai.MODEL}): {stats}")


def _clean_digest(d):
    """Iz starijih pregleda izbacuje tačke bez subjekta ili o "nevezanim" vestima i skida redne brojeve ("1. ")."""
    import local_ai
    en, sr = d.get("en") or [], d.get("sr") or d.get("en") or []
    keep = [i for i, x in enumerate(en) if local_ai.good_point(re.sub(r"^\s*\d+[.)]\s*", "", x))]
    strip = lambda x: _cap(re.sub(r"^\s*\d+[.)]\s*", "", x or ""))
    d["en"] = [strip(en[i]) for i in keep]
    d["sr"] = [strip(sr[i]) if i < len(sr) else strip(en[i]) for i in keep]
    return d


def _retranslate_digest(con, key, d):
    """AI pregled je napisan na engleskom - kad se promene pravila prevoda, srpska verzija se pravi ponovo."""
    import translate_fix
    if d.get("en") and d.get("v") != translate_fix.TR_VERSION:
        try:
            d["sr"] = [t for t, _ in ai._free_translate([(x, "") for x in d["en"]], "sr")]
            d["v"] = translate_fix.TR_VERSION
            db.set_meta(con, key, json.dumps(d, ensure_ascii=False))
        except Exception:  # noqa: BLE001
            pass
    return _clean_digest(d) if d.get("en") else d


def retranslate_findings(con, limit=300):
    """Nalazi studija (engleski rezultat + doprinos) ponovo na srpski kad se promene pravila prevoda."""
    import translate_fix
    if db.get_meta(con, "findings_tr_v") == translate_fix.TR_VERSION:
        return
    rows = con.execute("SELECT e.item_id, e.content FROM article_ai e WHERE e.kind='finding4' AND e.lang='en' AND NOT EXISTS "
                       "(SELECT 1 FROM meta m WHERE m.key = 'ftr_' || e.item_id AND m.value = ?) LIMIT ?",
                       (translate_fix.TR_VERSION, limit)).fetchall()
    if not rows:
        db.set_meta(con, "findings_tr_v", translate_fix.TR_VERSION)
        return
    parts = []
    for r in rows:
        res, _, con_ = r["content"].partition("\n\nKey contribution: ")
        parts.append((res, con_))
    try:
        tr = ai._free_translate(parts, "sr")
    except Exception:  # noqa: BLE001
        return
    for r, (res, c), (tres, tc) in zip(rows, parts, tr):
        if tres and tres != res:
            db.save_article_ai(con, r["item_id"], "sr", "finding4", tres + (f"\n\nKljučni doprinos: {tc or c}" if c else ""))
        db.set_meta(con, "ftr_" + r["item_id"], translate_fix.TR_VERSION)
    log(f"nalazi studija ponovo prevedeni: {len(rows)}")


def ai_digests(con):
    out = {}
    for sec in SECTIONS:
        for p in (1, 7, 30):
            try:
                d = _retranslate_digest(con, f"ai_digest_{sec}_{p}", json.loads(db.get_meta(con, f"ai_digest_{sec}_{p}") or "{}"))
            except ValueError:
                continue
            if d.get("en"):
                out.setdefault(sec, {})[str(p)] = {"en": d["en"], "sr": d.get("sr") or d["en"], "ids": d.get("ids", []), "at": d.get("at")}
    return out


def compact(it, trs, full, extra=None, lean=False, briefs=None):
    d = {"id": it["id"], "s": it["source"], "c": it.get("category") or "Vesti", "l": it.get("lang") or "en", "t": it["title"], "u": it.get("link"),
         "p": it["published"], "k": round(it.get("score") or 0, 2)}
    if not lean:
        d["d"] = (it.get("summary") or "")[:450]
    tr = trs.get(it["id"])
    if tr:
        d["tr"] = {k: ([v[0]] if lean else v) for k, v in tr.items()}
    if it["id"] in full:
        d["f"] = 1
    if briefs and not lean and briefs.get(it["id"]):
        d["b"] = briefs[it["id"]]
    if extra and extra.get(it["id"]):
        d["x"] = extra[it["id"]]
    if it.get("ticker"):
        d["tk"] = it["ticker"]
    return d


def theme_counts(items, themes):
    out = {}
    for sr, en, rx in themes:
        r_ = re.compile(rx, re.I)
        out[sr] = sum(1 for x in items if r_.search(x["title"] + " " + (x.get("summary") or "")[:300]))
    return out


def export_news(con):
    t0 = now()
    rows = db.query_items(con, start_iso=iso(t0 - timedelta(days=185)), exclude_categories=[RESEARCH], order="date", limit=200000)
    ids = [r["id"] for r in rows]
    trs = tr_map(con, ids)
    full = full_ids(con, ids)
    recent_cut = iso(t0 - timedelta(days=8))
    recent = [r for r in rows if r["published"] >= recent_cut]
    briefs = brief_map(con, [r["id"] for r in recent])
    size = dump("news/recent.json", [compact(r, trs, full, briefs=briefs) for r in recent])
    months = {}
    for r in rows:
        if r["published"] < recent_cut:
            months.setdefault(r["published"][:7], []).append(r)
    for m, lst in months.items():
        dump(f"news/{m}.json", [compact(r, trs, full, lean=True) for r in lst])
    log(f"vesti: {len(recent)} skorašnjih ({size // 1024} KB), {len(months)} meseci arhive")

    # sažeci perioda po sekcijama
    periods, needed = {}, {}
    for sec, cats in SECTIONS.items():
        periods[sec] = {}
        for p in PERIODS:
            a, b = iso(t0 - timedelta(days=p)), iso(t0 - timedelta(days=2 * p))
            pool = sorted([r for r in rows if r["category"] in cats and r["published"] >= a], key=lambda x: -(x["score"] or 0))
            prev = [r for r in rows if r["category"] in cats and b <= r["published"] < a]
            top, extra = dedupe(pool, 8)
            cn, cp = theme_counts(pool, SEC_THEMES[sec]), theme_counts(prev, SEC_THEMES[sec])
            en = {s: e for s, e, _ in SEC_THEMES[sec]}
            themes = sorted([[k, en[k], v, cp.get(k, 0)] for k, v in cn.items() if v], key=lambda x: -x[2])[:8]
            periods[sec][p] = {"top": [[x["id"], extra.get(x["id"], 0)] for x in top], "themes": themes, "n": len(pool),
                               "nsrc": len({x["source"] for x in pool}), "prev": len(prev)}
            for x in top:
                needed[x["id"]] = x
    digests = ai_digests(con)
    strategy = {}
    for p in ("1", "7"):
        try:
            st = json.loads(db.get_meta(con, f"ai_strategy_{p}") or "{}")
        except ValueError:
            st = {}
        if st.get("en"):
            strategy[p] = {"en": st["en"], "sr": st.get("sr") or st["en"], "ids": st.get("ids", []), "at": st.get("at"), "model": st.get("model")}
            digests.setdefault("_strategy", {})[p] = {"ids": st.get("ids", [])}
    for sec_d in digests.values():
        for d in sec_d.values():
            for i in d["ids"]:
                if i not in needed:
                    r = next((x for x in rows if x["id"] == i), None)
                    if r:
                        needed[i] = r
    pb = brief_map(con, needed.keys())
    trs.update(tr_map(con, [k for k in needed if k not in trs]))
    digests.pop("_strategy", None)
    dump("periods.json", {"periods": periods, "digests": digests, "strategy": strategy, "items": {k: compact(v, trs, full, briefs=pb) for k, v in needed.items()}})


def export_texts(con, days=30):
    """Celi tekstovi i 'Najvažnije' - samo za privatni repozitorijum."""
    since = iso(now() - timedelta(days=days))
    rows = con.execute("SELECT a.item_id, a.url, a.text, a.status, i.published FROM articles a JOIN items i ON i.id = a.item_id "
                       "WHERE i.published >= ? AND (a.status = 'ok' OR a.status LIKE 'alt:%')", (since,)).fetchall()
    by_day = {}
    for r in rows:
        q = {lang: db.get_article_ai(con, r["item_id"], lang, "quick") for lang in ("sr", "en")}
        fsr = db.get_article_ai(con, r["item_id"], "sr", "full")
        d = {"x": r["text"], "u": r["url"], "q": {k: v for k, v in q.items() if v}}
        if fsr:
            d["sr"] = fsr
        if r["status"].startswith("alt:"):
            d["a"] = r["status"][4:]
        by_day.setdefault(r["published"][:10], {})[r["item_id"]] = d
    return by_day


def brief_for(con, r):
    """Kratak opis kompanije: prve rečenice Yahoo opisa, prevedene na srpski (keširano)."""
    import universe
    if r["ticker"] in universe.EXTRA_BRIEF:
        sr, en = universe.EXTRA_BRIEF[r["ticker"]]
        return {"sr": sr, "en": en}
    txt = re.sub(r"\s+", " ", r.get("summary") or "").strip()
    if not txt:
        return None
    sents = re.split(r"(?<=[.!?])\s+", txt)
    out = []
    for x in sents:
        if out and (len(" ".join(out + [x])) > 480 or len(out) >= 3):
            break
        out.append(x)
    en = " ".join(out)
    key = "stk_" + r["ticker"]
    sr = db.get_article_ai(con, key, "sr", "brief4")
    if not sr:
        try:
            out = ai._free_translate([(en, "")], "sr")[0][0]
            if out and out != en:
                db.save_article_ai(con, key, "sr", "brief4", out)
                sr = out
        except Exception:  # noqa: BLE001
            pass
    return {"sr": sr or en, "en": en}


def about_for(con, r, max_chars=900):
    """Duži opis kompanije (do ~6 rečenica) i njegov prevod na srpski, keširano u bazi."""
    txt = re.sub(r"\s+", " ", r.get("summary") or "").strip()
    if not txt:
        return {"en": ""}
    out, n = [], 0
    for sent in re.split(r"(?<=[.!?])\s+", txt):
        if out and (n + len(sent) > max_chars or len(out) >= 6):
            break
        out.append(sent)
        n += len(sent) + 1
    en = " ".join(out)
    key = "stk_" + r["ticker"]
    sr = db.get_article_ai(con, key, "sr", "about3")
    if not sr and not about_for.failed:
        try:
            tr = ai._free_translate([(en, "")], "sr")[0][0]
            if tr and tr != en:
                db.save_article_ai(con, key, "sr", "about3", tr)
                sr = tr
        except Exception:  # noqa: BLE001
            about_for.failed += 1  # mreža za prevod ne radi - ne pokušavaj ponovo za svaku akciju
    return {"en": en, "sr": sr}


about_for.failed = 0


def export_stocks(con):
    import universe
    listings = stocks.listings(con)
    rows = stocks.metrics(con)
    ranked = stocks.apply_tax_preferences(stocks.score([dict(r) for r in rows]), con)
    smap = {r["ticker"]: r for r in ranked}
    themes = signals.theme_momentum(con, 7)
    opps = {o["ticker"]: o for o in signals.opportunities(con, rows, themes)}
    trs = tr_map(con, [n["id"] for o in opps.values() for n in o["catalysts"] + o["negatives"]])
    etf_holdings = stocks.etf_holdings(con)
    etf_weights = stocks.etf_sectors(con, set(stocks.ETFS) | set(stocks.ETF_PRIMARY_SECTOR))
    out = []
    for r in rows:
        o = opps.get(r["ticker"])
        rk = smap.get(r["ticker"])
        d = {k: (round(v, 5) if isinstance(v, float) else v) for k, v in r.items()
             if k in ("ticker", "name", "sector", "currency", "price", "date", "r1d", "r1w", "r1m", "r6m", "r1y", "vol", "mdd", "sma50",
                      "sma200", "pe", "peg", "roe", "margin", "de", "growth", "div", "mcap", "beta", "fcf_yield", "target", "upside", "rec", "analysts", "etf")}
        about = about_for(con, r)
        d["about"] = about["en"]
        if about.get("sr"):
            d["about_sr"] = about["sr"]
        if d.get("etf"):
            d["etf_sector"] = stocks.ETF_SECTORS.get(r["ticker"]) or r.get("fund_category") or "ETF"
            d["fund"] = {"family": r.get("fund_family"), "category": r.get("fund_category"),
                         "expense_ratio": r.get("fund_expense_ratio"), "assets": r.get("fund_assets")}
            d["holdings"] = etf_holdings.get(r["ticker"], [])
            w = etf_weights.get(r["ticker"]) or {}
            prim = stocks.etf_primary_sector(r["ticker"], w)
            if prim:
                d["etf_primary"] = prim
            if w:
                d["etf_weights"] = {k: round(v, 4) for k, v in list(w.items())[:6]}
        for k in ("fpe", "tpe", "ps"):
            if r.get(k) is not None:
                d[k] = round(r[k], 2)
        d["industry"] = r.get("industry") or ""
        d["industry_sr"] = universe.INDUSTRY_SR.get(d["industry"], "")
        u = universe.entry(r["ticker"])
        if u:
            d["theme"], d["tier"], d["brief"] = u[2], u[3], {"sr": u[4], "en": u[5]}
            # kratak opis u kartici: ručno napisana suština + prva rečenica opisa kompanije (2-3 rečenice ukupno)
            def first(txt):
                sents = re.split(r"(?<=[.!?])\s+(?=[A-ZČĆŠŽĐ])", txt or "")
                return sents[0] if sents and 40 <= len(sents[0]) <= 240 else ""
            fe, fs = first(about.get("en")), first(about.get("sr"))
            if fe and fs:
                d["brief"] = {"sr": f"{u[4]} {fs}", "en": f"{u[5]} {fe}"}
        else:
            d["theme"] = stocks.ETF_THEMES.get(r["ticker"]) or ("europe" if "." in r["ticker"] else "core")
            d["tier"] = "core"
            d["brief"] = brief_for(con, r)
        lst = listings.get(r["ticker"]) or {}
        if lst.get("x"):
            xs = stocks.series(con, lst["x"], days=12)
            d["xetra"] = {"t": lst["x"], "ex": lst.get("ex", "XETRA"), "px": round(xs[-1][1], 3) if xs else None,
                          "r1d": round(xs[-1][1] / xs[-2][1] - 1, 5) if len(xs) > 1 else None}
        if lst.get("isin"):
            d["isin"] = lst["isin"]
        d["spark"] = [float(f"{x:.5g}") for x in (r.get("spark") or [])[-90:]]
        try:
            news_digest = json.loads(db.get_meta(con, f"ai_company_news_7d_{r['ticker']}") or "{}")
        except ValueError:
            news_digest = {}
        if news_digest.get("en") and news_digest.get("ids"):
            d["ai_news"] = {k: news_digest[k] for k in ("en", "sr", "ids", "count", "at") if k in news_digest}
        if rk:
            d["score"] = rk["score"]
            d["region"] = rk.get("region")
            d["parts"] = {k: round(v, 3) for k, v in rk["parts"].items()}
            d["why"] = {"sr": stocks.reasons(rk, "sr"), "en": stocks.reasons(rk, "en")}
        if o:
            d.update({"opp": o["opp"], "qual": bool(o["qualifies"]), "dd": round(o["dd"], 4), "rsi": o["rsi"] and round(o["rsi"], 1),
                      "sent": o["sent"], "tail": round(o["tail"], 3),
                      "reasons": {lg: [signals.text(c, v, lg, signals.REASON_TXT) for c, v in o["reasons"]] for lg in ("sr", "en")},
                      "risks": {lg: [signals.text(c, v, lg, signals.RISK_TXT) for c, v in o["risks"]] for lg in ("sr", "en")},
                      "news": [dict(compact(n, trs, set()), pos=n in o["catalysts"]) for n in o["catalysts"] + o["negatives"]],
                      "themes": o["themes"], "setup": o["setup"], "above200": bool(o["above200"]), "golden": bool(o["golden"]),
                      "death": bool(o["death"]),
                      "setup_txt": {"sr": signals.SETUP_TXT[o["setup"]][0], "en": signals.SETUP_TXT[o["setup"]][1]},
                      "check": [[signals.CHECK_TXT[k][0], signals.CHECK_TXT[k][1], v] for k, v in o["checklist"]]})
        d["sector_sr"] = signals.SECTOR_SR.get(r.get("sector") or "", r.get("sector") or "")
        inf = stocks.info(con, r["ticker"])
        for key, field in (("earn", "earningsTimestampStart"), ("earn", "earningsTimestamp"), ("exdiv", "exDividendDate")):
            ts = inf.get(field)
            if ts and key not in d:
                try:
                    day = datetime.fromtimestamp(int(ts), timezone.utc).date()
                except (TypeError, ValueError, OSError):
                    continue
                if date.today() - timedelta(days=1) <= day <= date.today() + timedelta(days=75):
                    d[key] = day.isoformat()
        if d.get("earn") and inf.get("isEarningsDateEstimate"):
            d["earn_est"] = True
        out.append(d)
    tw = signals.sector_tailwind(themes)
    th = [{"sr": t["sr"], "en": t["en"], "n": t["n"], "prev": round(t["prev"], 1), "ratio": round(t["ratio"], 2), "why_sr": t["why_sr"],
           "why_en": t["why_en"], "effects": t["effects"], "items": [compact(x, tr_map(con, [x["id"]]), set()) for x in t["items"][:3]]}
          for t in themes]
    top = [d["ticker"] for d in sorted([d for d in out if d.get("opp") is not None], key=lambda d: (-d.get("qual", False), -d["opp"]))][:25]
    etf_map = {t: {"p": stocks.etf_primary_sector(t, etf_weights.get(t))} for t in set(stocks.ETF_PRIMARY_SECTOR) | set(etf_weights)}
    for t, v in etf_map.items():
        if etf_weights.get(t):
            v["w"] = {k: round(x, 4) for k, x in list(etf_weights[t].items())[:6]}
    dump("stocks.json", {"stocks": out, "etf_sectors": {t: v for t, v in etf_map.items() if v["p"]}, "themes": th, "tailwind": tw, "sectors_sr": signals.SECTOR_SR, "top20": top[:20], "top25": top,
                         "theme_names": universe.THEMES, "tiers": universe.TIERS, "tier_size": signals.TIER_SIZE,
                         "factors": [[k, w, sr, en] for k, w, _, sr, en in stocks.FACTORS]})
    # cene: do 30 godina dnevno za sve hartije, tržišta i kurseve
    tick = set(stocks.price_tickers(con)) | {t for t, _, _ in stocks.MARKETS} | {"EURUSD=X", "EURRSD=X", "GC=F"}
    since = (date.today() - timedelta(days=30 * 365)).isoformat()
    prices = {}
    for t in sorted(tick):
        s = [(r["d"], r["close"]) for r in con.execute("SELECT d, close FROM prices WHERE ticker=? AND d >= ? ORDER BY d", (t, since))]
        if s:
            prices[t] = {"d0": s[0][0], "d": [x[0][5:] if i and x[0][:4] == s[i - 1][0][:4] else x[0] for i, x in enumerate(s)],
                         "c": [float(f"{x[1]:.6g}") for x in s]}
    sz = dump("prices_all.json", prices)
    # mali fajl za Početnu i Portfolio: tržišta, kursevi, zlato i hartije iz portfolija (i njihove Xetra oznake)
    import portfolio
    core = {t for t, _, _ in stocks.MARKETS} | {"EURUSD=X", "EURRSD=X", "GC=F"} | set(portfolio.tickers(con))
    core |= {(listings.get(t) or {}).get("x") for t in portfolio.tickers(con)}
    dump("prices.json", {t: v for t, v in prices.items() if t in core})
    log(f"akcije: {len(out)}, prilika {sum(1 for x in out if x.get('qual'))}, cene {len(prices)} ({sz // 1024} KB)")


def export_research(con):
    import research
    since = (date.today() - timedelta(days=185)).isoformat()
    pool, seen = [], set()  # radovi za doktorat idu do 24 meseca unazad (lista po temama i periodima)
    for p in db.phd_papers(con, limit=400):
        if p["id"] not in seen:
            pool.append(dict(p, kind="phd")); seen.add(p["id"])
    for tag in ("cited_6m", "cited_24m", "journals", "latest"):
        try:
            for p in db.papers_by_tag(con, tag, limit=120):
                if p["id"] not in seen:
                    pool.append(dict(p, kind=tag)); seen.add(p["id"])
        except Exception:  # noqa: BLE001
            pass
    for it in db.query_items(con, start_iso=iso(now() - timedelta(days=185)), categories=[RESEARCH], order="score", limit=300):
        if it["id"] not in seen:
            pool.append({"id": it["id"], "title": it["title"], "venue": it["source"], "authors": "", "cited_by": None,
                         "pub_date": it["published"][:10], "link": it["link"], "abstract": reader.clean_abstract(it.get("summary")),
                         "kind": "feed", "phd_score": 0}); seen.add(it["id"])
    recent = [p for p in pool if (p.get("pub_date") or "") >= since]
    recent.sort(key=lambda p: -(p.get("phd_score") or 0) - (p.get("cited_by") or 0) / 200)
    work = recent[:420]  # sve skorije studije dobijaju nalaz, ne samo najvažnije
    for lang in ("sr", "en"):
        have = {p["id"]: db.get_article_ai(con, p["id"], lang, "finding4") for p in work}
        missing = [p for p in work if not have[p["id"]]][:160]
        if missing:
            for p in missing:
                a = db.get_article(con, p["id"])
                p["conclusion"] = a["text"] if a and a["status"] == "concl" else ""
            for pid, f in ai.findings(missing, lang).items():
                if f:
                    db.save_article_ai(con, pid, lang, "finding4", f)
    trs = tr_map(con, [p["id"] for p in pool])
    out = []
    for p in pool:
        f = {lang: db.get_article_ai(con, p["id"], lang, "finding4") for lang in ("sr", "en")}
        out.append({"id": p["id"], "t": p["title"], "ts": (trs.get(p["id"], {}).get("sr") or [None])[0], "v": p.get("venue") or "",
                    "a": (p.get("authors") or "")[:120], "y": p.get("pub_date") or str(p.get("year") or ""), "c": p.get("cited_by"),
                    "u": p.get("link"), "f": {k: v for k, v in f.items() if v}, "k": p.get("kind"),
                    "tp": [x for x in (p.get("topics") or "").split("|") if x], "ps": round(p.get("phd_score") or 0, 2),
                    "ab": (p.get("abstract") or "")[:900]})
    try:
        log("broj radova po temama:", research.refresh_topic_counts(con))
    except Exception as ex:  # noqa: BLE001
        log("! broj radova po temama:", ex)
    topics = []
    for t in research.phd_topics():
        row = {"q": t["q"], "sr": t["sr"], "en": t["en"]}
        try:
            c = json.loads(db.get_meta(con, f"topic_counts_{t['q']}") or "{}")
            if c:
                row["n"] = c
        except ValueError:
            pass
        topics.append(row)
    classics = json.loads((Path(__file__).parent / "classics.json").read_text(encoding="utf-8"))
    for p in RESEARCH_PERIODS:
        cut = (date.today() - timedelta(days=p)).isoformat()
        log(f"studije sa nalazom za {p} dana:", sum(1 for x in out if x["f"] and (x["y"] or "") >= cut), "od", sum(1 for x in out if (x["y"] or "") >= cut))
    rdig = {}
    for p in RESEARCH_PERIODS:
        try:
            d = _retranslate_digest(con, f"ai_rdigest_{p}", json.loads(db.get_meta(con, f"ai_rdigest_{p}") or "{}"))
        except ValueError:
            d = {}
        if d.get("en"):
            rdig[str(p)] = {"en": [_cap(x) for x in d["en"]], "sr": [_cap(x) for x in (d.get("sr") or d["en"])], "ids": d.get("ids", []), "at": d.get("at")}
    dump("research.json", {"papers": out, "topics": topics, "classics": classics, "digests": rdig})
    log(f"radovi: {len(out)}")


def export_meta(con):
    mtick = {name: t for t, name, _ in stocks.MARKETS}
    strip = [{"n": n, "v": v, "ch": c, "dec": d, "t": mtick.get(n)} for n, v, c, d in stocks.market_strip(con)]
    tk = {r["ticker"]: r["c"] for r in con.execute("SELECT ticker, COUNT(*) c FROM items WHERE ticker IS NOT NULL GROUP BY ticker")}
    dump("meta.json", {"generated": iso(now()), "last_fetch": db.get_meta(con, "last_fetch"), "markets": strip,
                       "data_repo": os.environ.get("FINNEWS_REPO") or ai.load_config().get("github_repo") or "",
                       "sources": sorted({f["name"] for f in fetcher.load_feeds() if f.get("enabled", True)}),
                       "watchlist": [[t, n] for t, n in stocks.watchlist()], "ticker_news": tk,
                       "market_list": [[t, n, d] for t, n, d in stocks.MARKETS],
                       "months": sorted(p.stem for p in (OUT / "news").glob("20*.json"))})


def push_texts(by_day):
    """Celi tekstovi idu u granu 'texts' privatnog repozitorijuma (bez istorije, samo poslednjih 30 dana)."""
    tok, repo = os.environ.get("GITHUB_TOKEN"), os.environ.get("FINNEWS_REPO")
    if not tok or not repo:
        local = OUT.parent.parent / "private_texts"
        for d, v in by_day.items():
            (local / "texts").mkdir(parents=True, exist_ok=True)
            (local / "texts" / f"{d}.json").write_text(json.dumps(v, ensure_ascii=False), encoding="utf-8")
        log(f"tekstovi (lokalno): {sum(len(v) for v in by_day.values())}")
        return
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "texts").mkdir()
        for d, v in by_day.items():
            (Path(tmp) / "texts" / f"{d}.json").write_text(json.dumps(v, ensure_ascii=False), encoding="utf-8")
        (Path(tmp) / "index.json").write_text(json.dumps(sorted(by_day)), encoding="utf-8")
        g = ["git", "-C", tmp, "-c", "user.name=FinNews", "-c", "user.email=finnews@users.noreply.github.com"]
        subprocess.run(["git", "init", "-q", "-b", "texts", tmp], check=True)
        subprocess.run(g + ["add", "."], check=True)
        subprocess.run(g + ["commit", "-qm", "texts"], check=True)
        r = subprocess.run(g + ["push", "-q", "-f", f"https://x-access-token:{tok}@github.com/{repo}.git", "texts"],
                           capture_output=True, text=True)
        log("tekstovi:", "poslato" if r.returncode == 0 else f"greška {r.stderr[-200:]}")


def main():
    con = db.connect()
    try:
        import cloud_sync
        if cloud_sync.enabled():
            log("portfolio/lista akcija:", cloud_sync.pull(con))
    except Exception as ex:  # noqa: BLE001
        log("! sinhronizacija:", ex)
    if "--export-only" not in sys.argv:
        refresh(con)
    OUT.mkdir(parents=True, exist_ok=True)
    for step in (export_news, export_stocks, export_research, export_meta):
        try:
            step(con)
        except Exception as ex:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            log(f"! {step.__name__}: {ex}")
            if step is export_stocks:
                raise
    try:
        push_texts(export_texts(con))
    except Exception as ex:  # noqa: BLE001
        log("! tekstovi:", ex)


if __name__ == "__main__":
    main()
