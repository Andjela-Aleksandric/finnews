"""Jutarnje obaveštenje: osveži vesti, (sa API ključem) pripremi dnevni brief i pošalji
macOS notifikaciju sa 3 najvažnije vesti."""
import shutil
import subprocess
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

APP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP))

import ai  # noqa: E402
import db  # noqa: E402
import fetcher  # noqa: E402
from menubar import clean, dedupe, translated  # noqa: E402

URL = "http://localhost:8765"


def notify(title, message):
    tn = shutil.which("terminal-notifier") or next(
        (p for p in ["/opt/homebrew/bin/terminal-notifier", "/usr/local/bin/terminal-notifier"] if Path(p).exists()), None)
    if tn:  # klik na obaveštenje otvara FinNews
        subprocess.run([tn, "-title", title, "-message", message, "-open", URL, "-group", "finnews"], check=False)
    else:
        subprocess.run(["osascript", "-e", "on run argv", "-e",
                        "display notification (item 2 of argv) with title (item 1 of argv)",
                        "-e", "end run", title, message], check=False)


def main():
    con = db.connect()
    try:
        fetcher.fetch_all(con)
    except Exception:  # noqa: BLE001
        pass
    lang = ai.load_config().get("ui_lang", "sr")
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat(timespec="seconds")
    top = dedupe(db.query_items(con, start_iso=since, exclude_categories=["Istraživanja"], limit=60), 3)
    if not top:
        return
    tr = translated(con, top, lang)
    msg = "\n".join("• " + clean(tr.get(i["id"], i["title"]), 70) for i in top)

    if ai.has_key():  # brief spreman kad otvoriš aplikaciju
        today = date.today()
        if not db.get_brief(con, today.isoformat(), lang):
            s = datetime.combine(today, time.min).astimezone().astimezone(timezone.utc).isoformat(timespec="seconds")
            news = db.query_items(con, start_iso=s, exclude_categories=["Istraživanja"], limit=60)
            res = db.query_items(con, start_iso=s, categories=["Istraživanja"], order="date", limit=15)
            try:
                db.save_brief(con, today.isoformat(), lang, ai.daily_brief(today.strftime("%d.%m.%Y."), news, res, lang),
                              datetime.now(timezone.utc).isoformat(timespec="seconds"))
            except Exception:  # noqa: BLE001
                pass
    notify("FinNews · " + ("jutarnji pregled" if lang == "sr" else "morning briefing"), msg)


if __name__ == "__main__":
    main()
