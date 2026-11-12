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


def dump(name, obj):
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
def pretranslate(con, lang, hours=72, limit=600):
    since = iso(now() - timedelta(hours=hours))
    items = db.query_items(con, start_iso=since, limit=limit)
    have = db.get_translations(con, [i["id"] for i in items], lang)
    todo = [i for i in items if i["id"] not in have and (i.get("lang") or "en") != lang]
    ok = 0
    for k in range(0, len(todo), 60):
        chunk = todo[k:k + 60]
        for it, (tt, ss) in zip(chunk, ai.translate_items([(i["title"], (i.get("summary") or "")[:450]) for i in chunk], lang)):
            if tt and tt != it["title"]:
                db.save_translation(con, it["id"], lang, tt, ss)
                ok += 1
    log(f"prevod {lang}: {ok}/{len(todo)}" + (f" ({ai.LAST_ERROR})" if ai.LAST_ERROR else ""))


def refresh(con):
    import run_fetch
    cfg = ai.load_config()
    cfg["ui_lang"] = "sr"
    cfg.setdefault("auto_read", True)
    ai.save_config(cfg)
    run_fetch.run(con, log=lambda *a: log(*a))
    pretranslate(con, "sr")
    pretranslate(con, "en")
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
            out.setdefault(k, {})[lang] = [v["title"], (v.get("summary") or "")[:300]]
    return out


def full_ids(con, ids):
    return {k for k, v in reader.statuses(con, ids).items() if reader.is_full(v)}


def compact(it, trs, full, extra=None, lean=False):
    d = {"id": it["id"], "s": it["source"], "c": it.get("category") or "Vesti", "l": it.get("lang") or "en", "t": it["title"], "u": it.get("link"),
         "p": it["published"], "k": round(it.get("score") or 0, 2)}
    if not lean:
        d["d"] = (it.get("summary") or "")[:300]
    tr = trs.get(it["id"])
    if tr:
        d["tr"] = {k: ([v[0]] if lean else v) for k, v in tr.items()}
    if it["id"] in full:
        d["f"] = 1
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
    size = dump("news/recent.json", [compact(r, trs, full) for r in recent])
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
    dump("periods.json", {"periods": periods, "items": {k: compact(v, trs, full) for k, v in needed.items()}})


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
    en = " ".join(sents[:2])[:320]
    key = "stk_" + r["ticker"]
    sr = db.get_article_ai(con, key, "sr", "brief")
    if not sr:
        try:
            out = ai._free_translate([(en, "")], "sr")[0][0]
            if out and out != en:
                db.save_article_ai(con, key, "sr", "brief", out)
                sr = out
        except Exception:  # noqa: BLE001
            pass
    return {"sr": sr or en, "en": en}


def export_stocks(con):
    import universe
    listings = stocks.listings(con)
    rows = stocks.metrics(con)
    ranked = stocks.apply_tax_preferences(stocks.score([dict(r) for r in rows]), con)
    smap = {r["ticker"]: r for r in ranked}
    themes = signals.theme_momentum(con, 7)
    opps = {o["ticker"]: o for o in signals.opportunities(con, rows, themes)}
    trs = tr_map(con, [n["id"] for o in opps.values() for n in o["catalysts"] + o["negatives"]])
    out = []
    for r in rows:
        o = opps.get(r["ticker"])
        rk = smap.get(r["ticker"])
        d = {k: (round(v, 5) if isinstance(v, float) else v) for k, v in r.items()
             if k in ("ticker", "name", "sector", "currency", "price", "date", "r1d", "r1w", "r1m", "r6m", "r1y", "vol", "mdd", "sma50",
                      "sma200", "pe", "peg", "roe", "margin", "de", "growth", "div", "mcap", "fcf_yield", "target", "upside", "rec", "analysts", "etf")}
        d["about"] = (r.get("summary") or "")[:900]
        for k in ("fpe", "tpe", "ps"):
            if r.get(k) is not None:
                d[k] = round(r[k], 2)
        d["industry"] = r.get("industry") or ""
        d["industry_sr"] = universe.INDUSTRY_SR.get(d["industry"], "")
        u = universe.entry(r["ticker"])
        if u:
            d["theme"], d["tier"], d["brief"] = u[2], u[3], {"sr": u[4], "en": u[5]}
        else:
            d["theme"] = "europe" if "." in r["ticker"] else "core"
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
        out.append(d)
    tw = signals.sector_tailwind(themes)
    th = [{"sr": t["sr"], "en": t["en"], "n": t["n"], "prev": round(t["prev"], 1), "ratio": round(t["ratio"], 2), "why_sr": t["why_sr"],
           "why_en": t["why_en"], "effects": t["effects"], "items": [compact(x, tr_map(con, [x["id"]]), set()) for x in t["items"][:3]]}
          for t in themes]
    top = [d["ticker"] for d in sorted([d for d in out if d.get("opp") is not None], key=lambda d: (-d.get("qual", False), -d["opp"]))][:25]
    dump("stocks.json", {"stocks": out, "themes": th, "tailwind": tw, "sectors_sr": signals.SECTOR_SR, "top20": top[:20], "top25": top,
                         "theme_names": universe.THEMES, "tiers": universe.TIERS, "tier_size": signals.TIER_SIZE,
                         "factors": [[k, w, sr, en] for k, w, _, sr, en in stocks.FACTORS]})
    # cene: 2 godine dnevno za sve hartije, tržišta i kurseve
    tick = set(stocks.price_tickers(con)) | {t for t, _, _ in stocks.MARKETS} | {"EURUSD=X", "EURRSD=X", "GC=F"}
    since = (date.today() - timedelta(days=740)).isoformat()
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
    pool, seen = [], set()
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
    work = recent[:160]
    for lang in ("sr", "en"):
        have = {p["id"]: db.get_article_ai(con, p["id"], lang, "finding") for p in work}
        missing = [p for p in work if not have[p["id"]]][:60]
        if missing:
            for p in missing:
                a = db.get_article(con, p["id"])
                p["conclusion"] = a["text"] if a and a["status"] == "concl" else ""
            for pid, f in ai.findings(missing, lang).items():
                if f:
                    db.save_article_ai(con, pid, lang, "finding", f)
    trs = tr_map(con, [p["id"] for p in pool])
    out = []
    for p in pool:
        f = {lang: db.get_article_ai(con, p["id"], lang, "finding") for lang in ("sr", "en")}
        out.append({"id": p["id"], "t": p["title"], "ts": (trs.get(p["id"], {}).get("sr") or [None])[0], "v": p.get("venue") or "",
                    "a": (p.get("authors") or "")[:120], "y": p.get("pub_date") or str(p.get("year") or ""), "c": p.get("cited_by"),
                    "u": p.get("link"), "f": {k: v for k, v in f.items() if v}, "k": p.get("kind"),
                    "tp": [x for x in (p.get("topics") or "").split("|") if x], "ps": round(p.get("phd_score") or 0, 2),
                    "ab": (p.get("abstract") or "")[:900]})
    topics = [{"q": t["q"], "sr": t["sr"], "en": t["en"]} for t in research.phd_topics()]
    classics = json.loads((Path(__file__).parent / "classics.json").read_text(encoding="utf-8"))
    dump("research.json", {"papers": out, "topics": topics, "classics": classics})
    log(f"radovi: {len(out)}")


def export_meta(con):
    strip = [{"n": n, "v": v, "ch": c, "dec": d} for n, v, c, d in stocks.market_strip(con)]
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
    try:
        push_texts(export_texts(con))
    except Exception as ex:  # noqa: BLE001
        log("! tekstovi:", ex)


if __name__ == "__main__":
    main()
