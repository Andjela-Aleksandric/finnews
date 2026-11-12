"""Moj portfolio: transakcije, nalozi na čekanju, pozicije, vrednost i izloženost."""
from datetime import date, datetime, timedelta, timezone

import ai
import db

# Početno stanje (unosi se jednom, posle se menja u aplikaciji)
# Približna geografska izloženost fondova (udeo), za procenu ukupne izloženosti portfolija
EXPOSURE = {
    "EUNL.DE": {"SAD": 0.71, "Evropa": 0.15, "Japan": 0.06, "Ostala razvijena": 0.08},
    "SXR8.DE": {"SAD": 1.0},
    "IS3N.DE": {"Tržišta u razvoju": 1.0},
    "VWCE.DE": {"SAD": 0.62, "Evropa": 0.13, "Tržišta u razvoju": 0.10, "Japan": 0.06, "Ostala razvijena": 0.09},
    "EXSA.DE": {"Evropa": 1.0},
}
REGION_EN = {"SAD": "US", "Evropa": "Europe", "Japan": "Japan", "Ostala razvijena": "Other developed",
             "Tržišta u razvoju": "Emerging markets", "Ostalo": "Other"}
COUNTRY_REGION = {"US": "SAD", "DE": "Evropa", "FR": "Evropa", "NL": "Evropa", "IT": "Evropa", "ES": "Evropa", "BE": "Evropa",
                  "IE": "Evropa", "AT": "Evropa", "FI": "Evropa", "CH": "Evropa", "GB": "Evropa"}


def _personal_seed():
    """Početni portfolio za prvo pokretanje na Mac-u (personal_seed.json se ne objavljuje na GitHub-u)."""
    import json
    from pathlib import Path
    f = Path(__file__).parent / "personal_seed.json"
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
        return [tuple(x) for x in d.get("txns", [])], [tuple(x) for x in d.get("assets", [])]
    except (OSError, ValueError):
        return [], []


SEED, ASSET_SEED = _personal_seed()
EUR_RSD_FALLBACK = 117.2


def _init(con):
    con.execute("""CREATE TABLE IF NOT EXISTS assets(
        id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT, name TEXT, amount REAL, currency TEXT, rate REAL,
        start TEXT, maturity TEXT, gold_base REAL, created TEXT)""")
    if not db.get_meta(con, "assets_seeded"):
        for kind, name, amt, cur, rate in ASSET_SEED:
            con.execute("INSERT INTO assets(kind, name, amount, currency, rate, start, created) VALUES(?,?,?,?,?,?,?)",
                        (kind, name, amt, cur, rate, date.today().isoformat(), datetime.now(timezone.utc).isoformat()))
        con.commit()
        db.set_meta(con, "assets_seeded", "1")
    if not db.get_meta(con, "assets_v2"):  # zlato se vodi kao ulaganje u indeks zlata, dinari kao obveznice
        con.execute("UPDATE assets SET name='Zlato - indeks cene zlata (XAU/EUR)' WHERE kind='gold' AND name LIKE 'Fizi%'")
        con.execute("UPDATE assets SET kind='bond', name='Obveznice u dinarima - fiksni prinos' WHERE kind='savings'")
        con.commit()
        db.set_meta(con, "assets_v2", "1")
    con.execute("""CREATE TABLE IF NOT EXISTS txns(
        id INTEGER PRIMARY KEY AUTOINCREMENT, ticker TEXT, name TEXT, isin TEXT, side TEXT, qty REAL, price REAL,
        fee REAL DEFAULT 0, d TEXT, status TEXT, limit_price REAL, note TEXT, created TEXT)""")
    if not db.get_meta(con, "portfolio_seeded"):
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        for t, name, isin, side, qty, cost, status, lim in SEED:
            price = cost / qty if cost else None
            d = date.today().isoformat() if status == "pending" else None
            con.execute("INSERT INTO txns(ticker, name, isin, side, qty, price, fee, d, status, limit_price, created) "
                        "VALUES(?,?,?,?,?,?,0,?,?,?,?)", (t, name, isin, side, qty, price, d, status, lim, now))
        con.commit()
        db.set_meta(con, "portfolio_seeded", now)


def txns(con):
    _init(con)
    return [dict(r) for r in con.execute("SELECT * FROM txns ORDER BY COALESCE(d, '0000') DESC, id DESC")]


def add(con, ticker, name, isin, side, qty, price, fee, d, status, limit_price=None, note=""):
    _init(con)
    con.execute("INSERT INTO txns(ticker, name, isin, side, qty, price, fee, d, status, limit_price, note, created) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (ticker.strip().upper(), name.strip(), isin.strip().upper(), side, float(qty),
                 float(price) if price else None, float(fee or 0), d, status, limit_price, note,
                 datetime.now(timezone.utc).isoformat(timespec="seconds")))
    con.commit()
    touch(con)


def update(con, tid, **kw):
    """Izmena bilo kog polja transakcije."""
    for k, v in kw.items():
        if k in ("ticker", "name", "isin", "side", "qty", "price", "fee", "d", "status", "limit_price", "note"):
            if k in ("ticker", "isin") and v:
                v = str(v).strip().upper()
            con.execute(f"UPDATE txns SET {k}=? WHERE id=?", (v, tid))
    con.commit()
    touch(con)


def touch(con):
    """Beleži vreme poslednje izmene portfolija (za sinhronizaciju sa telefonom/cloud verzijom)."""
    db.set_meta(con, "portfolio_changed", datetime.now(timezone.utc).isoformat(timespec="seconds"))


def export_state(con):
    _init(con)
    return {"version": 1, "changed": db.get_meta(con, "portfolio_changed") or "",
            "txns": [{k: r[k] for k in ("ticker", "name", "isin", "side", "qty", "price", "fee", "d", "status", "limit_price", "note", "created")}
                     for r in txns(con)],
            "assets": [{k: a[k] for k in ("kind", "name", "amount", "currency", "rate", "start", "maturity", "gold_base", "created")}
                       for a in assets(con)]}


def import_state(con, st_):
    """Zamenjuje lokalni portfolio stanjem iz sinhronizacije."""
    _init(con)
    con.execute("DELETE FROM txns")
    con.execute("DELETE FROM assets")
    for t in st_.get("txns", []):
        con.execute("INSERT INTO txns(ticker, name, isin, side, qty, price, fee, d, status, limit_price, note, created) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                    tuple(t.get(k) for k in ("ticker", "name", "isin", "side", "qty", "price", "fee", "d", "status", "limit_price", "note", "created")))
    for a in st_.get("assets", []):
        con.execute("INSERT INTO assets(kind, name, amount, currency, rate, start, maturity, gold_base, created) VALUES(?,?,?,?,?,?,?,?,?)",
                    tuple(a.get(k) for k in ("kind", "name", "amount", "currency", "rate", "start", "maturity", "gold_base", "created")))
    con.commit()
    db.set_meta(con, "portfolio_changed", st_.get("changed") or "")


def fill(con, tid, price, fee, d):
    con.execute("UPDATE txns SET status='filled', price=?, fee=?, d=? WHERE id=?", (float(price), float(fee or 0), d, tid))
    con.commit()
    touch(con)


def delete(con, tid):
    con.execute("DELETE FROM txns WHERE id=?", (tid,))
    con.commit()
    touch(con)


def tickers(con):
    _init(con)
    return sorted({r["ticker"] for r in con.execute("SELECT DISTINCT ticker FROM txns")})


def names(con):
    _init(con)
    return {r["ticker"]: r["name"] for r in con.execute("SELECT ticker, name FROM txns")}


def positions(con):
    """Izvršene transakcije -> pozicije (metoda prosečne nabavne cene)."""
    pos = {}
    for tx in sorted((t for t in txns(con) if t["status"] == "filled"), key=lambda x: (x["d"] or "0000", x["id"])):
        p = pos.setdefault(tx["ticker"], {"ticker": tx["ticker"], "name": tx["name"], "isin": tx["isin"], "qty": 0.0,
                                          "cost": 0.0, "realized": 0.0, "fees": 0.0, "first": tx["d"]})
        fee = tx["fee"] or 0
        p["fees"] += fee
        if tx["side"] == "buy":
            p["qty"] += tx["qty"]
            p["cost"] += tx["qty"] * (tx["price"] or 0) + fee
        else:
            avg = p["cost"] / p["qty"] if p["qty"] else 0
            sold = min(tx["qty"], p["qty"])
            p["realized"] += sold * (tx["price"] or 0) - fee - sold * avg
            p["cost"] -= sold * avg
            p["qty"] -= sold
    return [p for p in pos.values() if p["qty"] > 1e-9]


def _closes(con, t, days=None):
    sql, args = "SELECT d, close FROM prices WHERE ticker=?", [t]
    if days:
        sql += " AND d >= ?"
        args.append((date.today() - timedelta(days=days)).isoformat())
    return [(r["d"], r["close"]) for r in con.execute(sql + " ORDER BY d", args)]


def fx_usd(con):
    """Koliko dolara vredi 1 evro (EURUSD), za preračun pozicija u dolarima."""
    c = _closes(con, "EURUSD=X")
    return c[-1][1] if c else None


def valuation(con, infos=None):
    """Vrednost svake pozicije u evrima, uz dnevnu promenu."""
    infos = infos or {}
    usd = fx_usd(con)
    out = []
    for p in positions(con):
        c = _closes(con, p["ticker"])
        cur = (infos.get(p["ticker"]) or {}).get("currency") or ("EUR" if "." in p["ticker"] else "USD")
        rate = (1 / usd) if (cur == "USD" and usd) else 1.0
        price = c[-1][1] if c else None
        prev = c[-2][1] if len(c) > 1 else None
        value = p["qty"] * price * rate if price else None
        r = dict(p, price=price, currency=cur, value=value, avg=p["cost"] / p["qty"] if p["qty"] else None,
                 pl=(value - p["cost"]) if value is not None else None,
                 pl_pct=(value / p["cost"] - 1) if value and p["cost"] else None,
                 day=(price / prev - 1) if price and prev else None,
                 day_eur=(p["qty"] * (price - prev) * rate) if price and prev else None,
                 spark=[x[1] for x in c[-90:]], price_date=c[-1][0] if c else None)
        out.append(r)
    tot = sum(r["value"] or 0 for r in out)
    for r in out:
        r["weight"] = (r["value"] or 0) / tot if tot else 0
    return sorted(out, key=lambda r: -(r["value"] or 0))


def exposure(vals, country_of):
    """Približna geografska izloženost celog portfolija."""
    agg = {}
    for r in vals:
        w = r["weight"]
        mix = EXPOSURE.get(r["ticker"]) or {COUNTRY_REGION.get(country_of(r["ticker"]), "Ostalo"): 1.0}
        for k, v in mix.items():
            agg[k] = agg.get(k, 0) + w * v
    return sorted(agg.items(), key=lambda x: -x[1])


def history(con, days=365):
    """Kretanje vrednosti sadašnjih pozicija kroz vreme (kao da su držane ceo period)."""
    pos = positions(con)
    usd_series = dict(_closes(con, "EURUSD=X", days))
    series = {}
    for p in pos:
        cur = "EUR" if "." in p["ticker"] else "USD"
        for d, c in _closes(con, p["ticker"], days):
            rate = 1.0
            if cur == "USD":
                fx = usd_series.get(d)
                if not fx:
                    continue
                rate = 1 / fx
            series.setdefault(d, {})[p["ticker"]] = p["qty"] * c * rate
    full = [(d, sum(v.values())) for d, v in sorted(series.items()) if len(v) == len(pos)]
    return full


# ---------- ostala imovina: zlato, štednja, gotovina ----------
def eur_rsd(con):
    c = _closes(con, "EURRSD=X")
    return c[-1][1] if c and 100 < c[-1][1] < 140 else EUR_RSD_FALLBACK


def gold_eur(con):
    """Cena zlata u evrima po unci (GC=F u dolarima / EURUSD)."""
    g, fx = _closes(con, "GC=F"), fx_usd(con)
    return g[-1][1] / fx if g and fx else None


def assets(con):
    _init(con)
    return [dict(r) for r in con.execute("SELECT * FROM assets ORDER BY id")]


def add_asset(con, kind, name, amount, currency, rate=None, start=None, maturity=None, track_gold=True):
    _init(con)
    base = gold_eur(con) if (kind == "gold" and track_gold) else None
    con.execute("INSERT INTO assets(kind, name, amount, currency, rate, start, maturity, gold_base, created) VALUES(?,?,?,?,?,?,?,?,?)",
                (kind, name, float(amount), currency, rate, start or date.today().isoformat(), maturity, base,
                 datetime.now(timezone.utc).isoformat()))
    con.commit()
    touch(con)


def update_asset(con, aid, **kw):
    for k, v in kw.items():
        if k in ("kind", "name", "amount", "currency", "rate", "start", "maturity", "gold_base"):
            con.execute(f"UPDATE assets SET {k}=? WHERE id=?", (v, aid))
    con.commit()
    touch(con)


def delete_asset(con, aid):
    con.execute("DELETE FROM assets WHERE id=?", (aid,))
    con.commit()
    touch(con)


def asset_values(con):
    """Vrednost svake stavke u evrima. Zlato prati cenu zlata od trenutka unosa; štednja dodaje obračunatu kamatu."""
    rsd = eur_rsd(con)
    g_now = gold_eur(con)
    out = []
    for a in assets(con):
        if a["kind"] == "gold" and not a["gold_base"] and g_now:  # prva cena zlata posle unosa postaje polazna
            update_asset(con, a["id"], gold_base=g_now)
            a["gold_base"] = g_now
        fx = (1 / rsd) if a["currency"] == "RSD" else 1.0
        base_eur = a["amount"] * fx
        value, extra = base_eur, None
        if a["kind"] == "gold" and a["gold_base"] and g_now:
            value = base_eur * g_now / a["gold_base"]
            extra = g_now / a["gold_base"] - 1
        if a["kind"] in ("savings", "bond") and a["rate"]:
            try:
                days = (date.today() - date.fromisoformat(a["start"])).days
            except (TypeError, ValueError):
                days = 0
            interest = a["amount"] * a["rate"] * max(0, days) / 365
            value = (a["amount"] + interest) * fx
            extra = interest
        out.append(dict(a, base_eur=base_eur, value=value, extra=extra, rsd=rsd))
    return out


def gold_series(con, days=365):
    """Indeks zlata u evrima po danima (GC=F / EURUSD)."""
    fx = dict(_closes(con, "EURUSD=X", days))
    return [(d, c / fx[d]) for d, c in _closes(con, "GC=F", days) if fx.get(d)]


def total_history(con, days=365):
    """Kretanje ukupne imovine: hartije + zlato (prati indeks zlata) + obveznice (linearan rast po stopi)."""
    sec = dict(history(con, days))
    gold = dict(gold_series(con, days))
    g_now = gold_eur(con)
    av = asset_values(con)
    out = []
    for d in sorted(sec):
        tot = sec[d]
        try:
            back = (date.today() - date.fromisoformat(d)).days
        except ValueError:
            back = 0
        for a in av:
            if a["kind"] == "gold" and g_now and gold.get(d):
                tot += a["value"] * gold[d] / g_now
            elif a["kind"] in ("bond", "savings") and a["rate"]:
                tot += a["value"] / (1 + a["rate"] * back / 365)
            else:
                tot += a["value"]
        out.append((d, sec[d], tot))
    return out
