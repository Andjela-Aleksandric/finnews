"""FinNews widget za menu bar (SwiftBar). Ispisuje meni u SwiftBar formatu:
najvažnije vesti u poslednja 24h, novi radovi i prečice."""
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

APP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP))

import ai  # noqa: E402
import db  # noqa: E402
import fetcher  # noqa: E402

URL = "http://localhost:8765"
L = {
    "sr": {"top": "NAJVAŽNIJE DANAS", "res": "NOVI RADOVI", "open": "Otvori FinNews", "refresh": "Osveži vesti",
           "brief": "Dnevni brief", "empty": "Još nema vesti - otvori FinNews", "upd": "Ažurirano"},
    "en": {"top": "TOP STORIES TODAY", "res": "NEW PAPERS", "open": "Open FinNews", "refresh": "Refresh news",
           "brief": "Daily brief", "empty": "No news yet - open FinNews", "upd": "Updated"},
}


def clean(s, n=78):
    s = re.sub(r"\s+", " ", (s or "").replace("|", "/")).strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def dedupe(items, limit):
    kept, toks = [], []
    for it in items:
        tk = fetcher.tokens(it["title"])
        if any(tk and len(tk & k) >= 3 and len(tk & k) / len(tk | k) >= 0.3 for k in toks):
            continue
        kept.append(it); toks.append(tk)
        if len(kept) >= limit:
            break
    return kept


def translated(con, items, lang):
    have = db.get_translations(con, [i["id"] for i in items], lang)
    missing = [i for i in items if i["id"] not in have and i.get("lang") != lang]
    if missing:
        try:
            for it, (t, s) in zip(missing, ai.translate_items([(i["title"], "") for i in missing], lang)):
                if t != it["title"]:
                    db.save_translation(con, it["id"], lang, t, "")
                    have[it["id"]] = {"title": t}
        except Exception:  # noqa: BLE001 - widget mora uvek da se prikaže
            pass
    return {k: v["title"] for k, v in have.items()}


def main():
    con = db.connect()
    lang = ai.load_config().get("ui_lang", "sr")
    tx = L[lang]
    now = datetime.now(timezone.utc)
    since = (now - timedelta(hours=24)).isoformat(timespec="seconds")
    news = dedupe(db.query_items(con, start_iso=since, exclude_categories=["Istraživanja"], limit=80), 8)
    papers = db.query_items(con, start_iso=(now - timedelta(days=7)).isoformat(timespec="seconds"),
                            categories=["Istraživanja"], order="score", limit=5)
    tr = translated(con, news + papers, lang)

    try:  # izmene sa telefona (cloud verzija) stižu i u menu bar
        import cloud_sync
        cloud_sync.pull(con)
    except Exception:  # noqa: BLE001
        pass
    pf = None
    try:
        import portfolio
        import stocks
        infos = {t: stocks.info(con, t) for t in portfolio.tickers(con)}
        vals = portfolio.valuation(con, infos)
        avals = portfolio.asset_values(con)
        gs = portfolio.gold_series(con, 12)
        g_day = gs[-1][1] / gs[-2][1] - 1 if len(gs) > 1 else 0
        tv = sum(v["value"] or 0 for v in vals) + sum(a["value"] or 0 for a in avals)
        tc = sum(v["cost"] for v in vals) + sum(a["base_eur"] for a in avals)
        td = sum(v["day_eur"] or 0 for v in vals) + sum((a["value"] or 0) * g_day for a in avals if a["kind"] == "gold")
        if tv:
            pf = (tv, tv / tc - 1 if tc else 0, td, vals, avals, g_day)
    except Exception:  # noqa: BLE001
        pass
    eur = (lambda x, d=0: (f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".") if lang == "sr" else f"{x:,.{d}f}") + " €")
    pc = (lambda x: (f"{x * 100:+.2f}%".replace(".", ",") if lang == "sr" else f"{x * 100:+.2f}%"))
    title = "📈" + (f" {len(news)}" if news else "")
    if pf:
        dp = abs(pf[2] / (pf[0] - pf[2]) * 100) if pf[0] != pf[2] else 0
        dps = f"{dp:.1f}%".replace(".", ",") if lang == "sr" else f"{dp:.1f}%"
        title = f"📈 {eur(pf[0])} {'▲' if pf[2] >= 0 else '▼'}{dps}"
    print(title)
    print("---")
    if pf:
        tv, ret, td, vals, avals, g_day = pf
        up, dn = "#7FB685", "#C2435F"
        print(f"PORTFOLIO | size=11 color={dn}")
        print(f"{eur(tv, 2)} | href={URL} font=Menlo size=14")
        print(f"{'Danas' if lang == 'sr' else 'Today'}  {'+' if td >= 0 else ''}{eur(td, 2)} | font=Menlo color={up if td >= 0 else dn}")
        print(f"{'Ukupno' if lang == 'sr' else 'Total'}  {pc(ret)} | font=Menlo color={up if ret >= 0 else dn}")
        print("---")
        for v in vals:
            nm = v["ticker"].replace(".DE", "")
            print(f"{nm:<6} {eur(v['value'] or 0):>11}  {pc(v['pl_pct'] or 0):>8} | font=Menlo size=12 color={up if (v['pl_pct'] or 0) >= 0 else dn} href={URL}")
            print(f"--{v['name'][:42]} | size=11")
            print(f"--{'danas' if lang == 'sr' else 'today'} {pc(v['day'] or 0)}  ·  {v['qty']:g} × {(v['price'] or 0):.2f} | size=11 font=Menlo")
        for a in avals:
            lbl = {"gold": "Zlato" if lang == "sr" else "Gold", "bond": "Obvezn." if lang == "sr" else "Bonds"}.get(a["kind"], a["kind"][:6])
            ch = (a["value"] or 0) / a["base_eur"] - 1 if a["base_eur"] else 0
            print(f"{lbl:<6} {eur(a['value'] or 0):>11}  {pc(ch):>8} | font=Menlo size=12 color={up if ch >= 0 else dn}")
        pend = [x for x in portfolio.txns(con) if x["status"] == "pending"]
        for o in pend:
            print(f"⏳ {o['ticker'].replace('.DE', '')} limit {o['limit_price'] or 0:.2f} € × {o['qty']:g} | size=11 color=#A8979A")
        print("---")
    print(f"{tx['top']} | size=11 color=#C2435F")
    if not news:
        print(f"{tx['empty']} | href={URL}")
    for it in news:
        t = clean(tr.get(it["id"], it["title"]))
        print(f"{t} | href={it['link']} tooltip={clean(it['source'], 40)}")
        print(f"--{clean(it['source'], 40)} · ⚡ {it['score']:.1f} | size=11 color=#A8979A")
    if papers:
        print("---")
        print(f"{tx['res']} | size=11 color=#A78BFA")
        for it in papers:
            print(f"{clean(tr.get(it['id'], it['title']))} | href={it['link']} tooltip={clean(it['source'], 40)}")
    print("---")
    print(f"{tx['open']} | href={URL}")
    print(f"{tx['refresh']} | bash={sys.executable} param1={APP / 'run_fetch.py'} terminal=false refresh=true")
    last = db.get_meta(con, "last_fetch")
    if last:
        print(f"{tx['upd']}: {datetime.fromisoformat(last).astimezone():%d.%m. %H:%M} | size=11 color=#A8979A")


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:  # noqa: BLE001
        print("📈 !")
        print("---")
        print(f"FinNews: {clean(str(ex), 60)}")
