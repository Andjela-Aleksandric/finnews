"""Sinhronizacija portfolija između Mac-a i FinNews-a na internetu (telefon kad je Mac ugašen).

Portfolio se čuva kao data/portfolio.json u PRIVATNOM GitHub repozitorijumu (npr. korisnik/finnews-data).
Obe strane (Mac i cloud) na otvaranju preuzimaju noviju verziju, a posle svake izmene šalju svoju.
Podešava se jednom komandom: bash ~/finnews/deploy_cloud.sh"""
import base64
import json
import os
import threading

import requests

import ai
import db
import portfolio

PATH = "data/portfolio.json"
API = "https://api.github.com/repos/{repo}/contents/" + PATH
_LOCK = threading.Lock()


def settings():
    cfg = ai.load_config()
    tok = os.environ.get("GITHUB_TOKEN") or cfg.get("github_token")
    repo = os.environ.get("FINNEWS_REPO") or cfg.get("github_repo")
    return (tok, repo) if tok and repo else (None, None)


def enabled():
    return all(settings())


def _headers(tok):
    return {"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}


def _get():
    tok, repo = settings()
    r = requests.get(API.format(repo=repo), headers=_headers(tok), timeout=15)
    if r.status_code == 404:
        return None, None
    r.raise_for_status()
    j = r.json()
    return json.loads(base64.b64decode(j["content"]).decode("utf-8")), j["sha"]


def _state(con):
    import stocks
    st_ = portfolio.export_state(con)
    st_["watchlist"] = [{"t": t, "name": n} for t, n in stocks.watchlist()]
    return st_


def push(con, sha=None):
    if not enabled():
        return "off"
    tok, repo = settings()
    with _LOCK:
        if sha is None:
            _, sha = _get()
        body = {"message": "FinNews: portfolio", "content": base64.b64encode(
            json.dumps(_state(con), ensure_ascii=False, indent=1).encode("utf-8")).decode()}
        if sha:
            body["sha"] = sha
        r = requests.put(API.format(repo=repo), headers=_headers(tok), json=body, timeout=20)
        r.raise_for_status()
    db.set_meta(con, "sync_ok", db.get_meta(con, "portfolio_changed") or "")
    return "pushed"


def push_async(con_factory):
    """Slanje u pozadini da izmena u aplikaciji ne čeka mrežu."""
    if not enabled():
        return

    def run():
        try:
            c = con_factory()
            push(c)
        except Exception as ex:  # noqa: BLE001
            try:
                db.set_meta(con_factory(), "sync_error", str(ex)[:200])
            except Exception:  # noqa: BLE001
                pass
    threading.Thread(target=run, daemon=True).start()


def pull(con):
    """Uzima noviju verziju (ili šalje lokalnu ako je ona novija). Vraća: off / pulled / pushed / same."""
    if not enabled():
        return "off"
    data, sha = _get()
    local = db.get_meta(con, "portfolio_changed") or ""
    if not data:
        return push(con)
    remote = data.get("changed") or ""
    if remote > local:
        portfolio.import_state(con, data)
        if data.get("watchlist"):
            import stocks
            stocks.save_watchlist("\n".join(f'{w["t"]} | {w["name"]}' for w in data["watchlist"]))
        db.set_meta(con, "sync_ok", remote)
        return "pulled"
    if local > remote:
        return push(con, sha)
    return "same"
