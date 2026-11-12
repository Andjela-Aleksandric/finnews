"""Pozadinsko osvežavanje: vesti, prevodi, celi tekstovi, sažeci, akcije i radovi.
Pokreće ga macOS launchd (na 30 min), a na serveru/hostingu nit iz same aplikacije (start_background)."""
import threading
import time
from datetime import datetime, timedelta, timezone

import ai
import db
import fetcher
import reader
import research
import stocks

_LOCK = threading.Lock()


def _stale(con, key, **delta):
    last = db.get_meta(con, key)
    return not last or datetime.now(timezone.utc) - datetime.fromisoformat(last) > timedelta(**delta)


def prepare_reading(con, lang, hours=36, limit=70, log=print):
    """Za najrelevantnije vesti: nabavi CEO tekst (original ili drugi izvor) i napravi trenutni sažetak."""
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat(timespec="seconds")
    items = db.query_items(con, start_iso=since, exclude_categories=["Istraživanja"], limit=400)
    items.sort(key=lambda x: -fetcher.relevance(x))
    full = part = 0
    for it in items[:limit]:
        try:
            art = reader.get_article(con, it)
            if reader.is_full(art["status"]):
                full += 1
                if not db.get_article_ai(con, it["id"], lang, "quick"):
                    q = ai.quick_summary(art["text"], lang, it.get("lang") or "en")
                    if q:
                        db.save_article_ai(con, it["id"], lang, "quick", q)
            else:
                part += 1
        except Exception:  # noqa: BLE001
            part += 1
    log(f"  celi tekstovi: {full} pronađeno, {part} bez celog teksta")


def run(con=None, log=print, light=False):
    """light=True: samo vesti, prevodi, tekstovi i cene (za hosting); bez nedeljnih teških poslova."""
    con = con or db.connect()
    res = fetcher.fetch_all(con)
    log(f"{datetime.now():%Y-%m-%d %H:%M} novih: {res['new']} / izvora: {res['sources']} / greške: {len(res['errors'])}")
    for name, err in res["errors"].items():
        log(f"  ! {name}: {err}")
    cfg = ai.load_config()
    lang = cfg.get("ui_lang", "sr")

    # prevod naslova unapred (oba jezika se prevode po potrebi; ovde jezik koji se koristi)
    since48 = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat(timespec="seconds")
    recent = db.query_items(con, start_iso=since48, limit=300)
    have = db.get_translations(con, [i["id"] for i in recent], lang)
    todo = [i for i in recent if i["id"] not in have and i.get("lang") != lang]
    ok = 0
    for k in range(0, len(todo), 40):
        chunk = todo[k:k + 40]
        for it, (tt, ss) in zip(chunk, ai.translate_items([(i["title"], i.get("summary") or "") for i in chunk], lang)):
            if tt != it["title"]:
                db.save_translation(con, it["id"], lang, tt, ss)
                ok += 1
    log(f"  prevedeno unapred: {ok}/{len(todo)}" + (f" (greška: {ai.LAST_ERROR})" if ai.LAST_ERROR else ""))

    if cfg.get("auto_read", True):
        prepare_reading(con, lang, log=log)

    try:  # portfolio sa telefona (cloud verzija)
        import cloud_sync
        if cloud_sync.enabled():
            log(f"  portfolio sinhronizacija: {cloud_sync.pull(con)}")
    except Exception as ex:  # noqa: BLE001
        log(f"  ! sinhronizacija: {ex}")
    try:  # akcije i traka tržišta
        stocks.refresh_info(con)
        stocks.refresh_listings(con)
        stocks.refresh_prices(con)
        if _stale(con, "stock_news_refreshed", hours=2):
            log(f"  vesti kompanija: +{stocks.refresh_news(con)}")
    except Exception as ex:  # noqa: BLE001
        log(f"  ! akcije: {ex}")
    if light:
        return res

    if not db.get_meta(con, "backfill_done"):
        b = fetcher.backfill(con, months=6)
        log(f"  arhiva 6 meseci: +{b['new']} (greške {b['errors']}/{b['requests']})")
    if _stale(con, "papers_refreshed", days=7):
        r = research.refresh(con)
        log(f"  radovi (OpenAlex): {r['jobs'] - r['errors']}/{r['jobs']} upita uspešno")
    if _stale(con, "phd_refreshed", days=7):
        r = research.refresh_phd(con)
        r2 = research.refresh_gaps(con)
        log(f"  doktorat radar: {r['steps'] - r['errors']}/{r['steps']}, mapa praznina: {r2['steps'] - r2['errors']}/{r2['steps']}")
    top_p = db.phd_papers(con, limit=25)
    for p in top_p:
        if not db.get_article(con, p["id"]):
            try:
                reader.get_paper(con, p)
            except Exception:  # noqa: BLE001
                pass
    todo_f = [p for p in top_p if not db.get_article_ai(con, p["id"], lang, "finding")]
    for p in todo_f:
        a = db.get_article(con, p["id"])
        p["conclusion"] = a["text"] if a and a["status"] == "concl" else ""
    for pid, f in ai.findings(todo_f, lang).items():
        if f:
            db.save_article_ai(con, pid, lang, "finding", f)
    log(f"  nalazi studija: {len(todo_f)}")
    return res


def start_background(interval_min=30):
    """Nit koja osvežava podatke kad niko drugi to ne radi (hosting, Docker, ili Mac bez launchd zadatka)."""
    def loop():
        time.sleep(20)
        while True:
            try:
                con = db.connect()
                if _stale(con, "last_fetch", minutes=interval_min + 10) and _LOCK.acquire(blocking=False):
                    try:
                        run(con, log=lambda *_: None)
                    finally:
                        _LOCK.release()
                con.close()
            except Exception:  # noqa: BLE001
                pass
            time.sleep(interval_min * 60)
    th = threading.Thread(target=loop, daemon=True, name="finnews-refresh")
    th.start()
    return th


if __name__ == "__main__":
    run()
