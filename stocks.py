"""Akcije: cene, osnovni pokazatelji, vesti o kompanijama i faktorski predlog atraktivnih akcija.
Podaci: Yahoo Finance preko biblioteke yfinance (besplatno, bez ključa)."""
import hashlib
import json
import math
from datetime import datetime, timedelta, timezone

import ai
import db
import eu

import universe  # noqa: E402

DEFAULT_WATCHLIST = list(eu.EU_WATCHLIST) + [(u[0], u[1]) for u in universe.UNIVERSE if u[0] not in {t for t, _ in eu.EU_WATCHLIST}]
WATCHLIST_VERSION = 2
ETFS = {"SPY", "QQQ", "VT", "GLD", "AGG", "SMH", "IWDA.AS"} | eu.EU_ETFS
# Traka tržišta u zaglavlju: (simbol, naziv, broj decimala)
MARKETS = [("^GSPC", "S&P 500", 0), ("^NDX", "Nasdaq 100", 0), ("^STOXX", "STOXX 600", 1), ("^GDAXI", "DAX", 0),
           ("EURUSD=X", "EUR/USD", 4), ("GC=F", "Zlato $", 0), ("BZ=F", "Brent $", 2), ("BTC-USD", "Bitcoin $", 0),
           ("^TNX", "US 10g %", 2), ("^VIX", "VIX", 1)]
INFO_KEYS = ["longName", "shortName", "sector", "industry", "currency", "marketCap", "trailingPE", "forwardPE",
             "pegRatio", "trailingPegRatio", "priceToBook", "returnOnEquity", "profitMargins", "debtToEquity",
             "revenueGrowth", "earningsGrowth", "dividendYield", "targetMeanPrice", "recommendationMean",
             "recommendationKey", "numberOfAnalystOpinions", "beta", "fiftyTwoWeekHigh", "fiftyTwoWeekLow",
             "longBusinessSummary", "priceToSalesTrailing12Months", "enterpriseToEbitda", "freeCashflow", "grossMargins",
             "operatingMargins", "returnOnAssets", "earningsQuarterlyGrowth", "currentRatio", "quickRatio", "totalCash",
             "totalDebt", "trailingAnnualDividendYield", "payoutRatio", "dividendRate", "exDividendDate",
             "lastDividendValue", "lastDividendDate", "country", "exchange", "fullExchangeName", "netExpenseRatio",
             "totalAssets", "fundFamily", "category"]
INFO_VERSION = 3


def _init(con):
    con.executescript("""
    CREATE TABLE IF NOT EXISTS prices(ticker TEXT, d TEXT, close REAL, PRIMARY KEY(ticker, d));
    CREATE TABLE IF NOT EXISTS stock_info(ticker TEXT PRIMARY KEY, info TEXT, updated TEXT);
    """)
    try:
        con.execute("ALTER TABLE items ADD COLUMN ticker TEXT")
    except Exception:  # noqa: BLE001 - kolona već postoji
        pass


def all_tickers(con):
    """Lista praćenja + hartije iz portfolija (bez duplikata)."""
    import portfolio
    out = [t for t, _ in watchlist()]
    out += [t for t in portfolio.tickers(con) if t not in out]
    return out


def watchlist():
    cfg = ai.load_config()
    wl = cfg.get("watchlist")
    if wl and cfg.get("wl_version", 1) < WATCHLIST_VERSION:  # jednom dodaj nove akcije na postojeću listu
        have = {x["t"] for x in wl}
        wl += [{"t": u[0], "name": u[1]} for u in universe.UNIVERSE if u[0] not in have]
        cfg["watchlist"], cfg["wl_version"] = wl, WATCHLIST_VERSION
        ai.save_config(cfg)
    if wl:
        return [(x["t"], x.get("name") or x["t"]) for x in wl]
    return DEFAULT_WATCHLIST


# ---------- iste akcije na Xetri (za trgovanje u evrima, npr. preko Erste brokera) ----------
def listings(con):
    try:
        return json.loads(db.get_meta(con, "listings") or "{}")
    except ValueError:
        return {}


def _name_tokens(s):
    import re
    stop = {"inc", "corp", "corporation", "co", "ltd", "plc", "holdings", "group", "the", "company", "class", "sa", "ag", "nv", "se", "adr"}
    return {w for w in re.findall(r"[a-z0-9]+", (s or "").lower()) if w not in stop and len(w) > 1}


def refresh_listings(con, max_new=200, max_age_days=30):
    """Za svaku akciju traži njenu oznaku na Xetri (npr. NVDA -> NVD.DE) preko Yahoo pretrage. Keširano mesec dana."""
    import yfinance as yf
    _init(con)
    lst = listings(con)
    now = datetime.now(timezone.utc)
    n = 0
    for t, name in watchlist():
        cur = lst.get(t)
        if cur and (now - datetime.fromisoformat(cur.get("at", "2000-01-01T00:00:00+00:00"))).days < max_age_days:
            continue
        if n >= max_new:
            break
        n += 1
        if t.endswith(".DE"):
            lst[t] = {"x": t, "ex": "XETRA", "at": now.isoformat(timespec="seconds")}
            continue
        inf = info(con, t)
        nm = inf.get("longName") or inf.get("shortName") or name
        best = None
        try:
            quotes = yf.Search(nm, max_results=20, news_count=0).quotes or []
        except Exception:  # noqa: BLE001
            quotes = []
        want = _name_tokens(nm) | _name_tokens(name)
        for exch, suffix in (("GER", ".DE"), ("FRA", ".F")):
            for q in quotes:
                sym = q.get("symbol") or ""
                if not sym.endswith(suffix) or q.get("quoteType") not in ("EQUITY", None):
                    continue
                if want & _name_tokens(q.get("shortname") or q.get("longname")):
                    best = {"x": sym, "ex": "XETRA" if suffix == ".DE" else "Frankfurt"}
                    break
            if best:
                break
        rec = dict(best or {}, at=now.isoformat(timespec="seconds"))
        if cur and cur.get("isin"):
            rec["isin"] = cur["isin"]
        lst[t] = rec
    # ISIN (za pretragu u brokeru) - sporiji izvor, pa najviše ~90 sekundi po pokretanju
    import time as _time
    t0 = _time.time()
    for t, _ in watchlist():
        rec = lst.get(t)
        if not rec or rec.get("isin") or rec.get("no_isin") or _time.time() - t0 > 90:
            continue
        try:
            isin = yf.Ticker(t).isin
        except Exception:  # noqa: BLE001
            isin = None
        if isin and isin != "-" and len(isin) == 12:
            rec["isin"] = isin
        else:
            rec["no_isin"] = 1
    db.set_meta(con, "listings", json.dumps(lst))
    return n


def price_tickers(con):
    """Sve hartije za koje se preuzimaju cene: lista, portfolio i njihove Xetra oznake."""
    out = all_tickers(con)
    for v in listings(con).values():
        if v.get("x") and v["x"] not in out:
            out.append(v["x"])
    return out


def save_watchlist(text):
    """text: red po akciji, 'TICKER' ili 'TICKER | Naziv'."""
    out = []
    for ln in text.splitlines():
        if not ln.strip():
            continue
        t, _, name = ln.partition("|")
        out.append({"t": t.strip().upper(), "name": name.strip() or t.strip().upper()})
    cfg = ai.load_config()
    cfg["watchlist"] = out
    ai.save_config(cfg)


# ---------- preuzimanje ----------
def refresh_prices(con=None):
    import yfinance as yf
    con = con or db.connect()
    _init(con)
    tickers = price_tickers(con) + ["EURUSD=X", "EURRSD=X", "GC=F"] + [m[0] for m in MARKETS if m[0] not in ("EURUSD=X", "GC=F")]
    df = yf.download(tickers, period="2y", interval="1d", auto_adjust=True, progress=False,
                     group_by="ticker", threads=True)
    n = 0
    for t in tickers:
        try:
            s = (df[t]["Close"] if len(tickers) > 1 else df["Close"]).dropna()
        except Exception:  # noqa: BLE001
            continue
        if hasattr(s, "columns"):
            s = s.iloc[:, 0]
        rows = [(t, idx.strftime("%Y-%m-%d"), float(v)) for idx, v in s.items() if v == v]
        if rows:
            con.executemany("INSERT OR REPLACE INTO prices VALUES(?,?,?)", rows)
            n += 1
    con.commit()
    db.set_meta(con, "prices_refreshed", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    return n


def refresh_info(con=None, max_age_h=20):
    import yfinance as yf
    con = con or db.connect()
    _init(con)
    now = datetime.now(timezone.utc)
    n = 0
    for t in all_tickers(con):
        row = con.execute("SELECT updated, info FROM stock_info WHERE ticker=?", (t,)).fetchone()
        if (row and now - datetime.fromisoformat(row["updated"]) < timedelta(hours=max_age_h)
                and json.loads(row["info"]).get("_v") == INFO_VERSION):
            continue
        try:
            info = yf.Ticker(t).info or {}
        except Exception:  # noqa: BLE001
            continue
        keep = {k: info.get(k) for k in INFO_KEYS if info.get(k) is not None}
        try:  # isplate dividendi u poslednje 2 godine
            dv = yf.Ticker(t).dividends
            cutoff = now - timedelta(days=730)
            keep["_divs"] = [[d.strftime("%Y-%m-%d"), float(a)] for d, a in dv.items()
                             if d.to_pydatetime().replace(tzinfo=d.tzinfo or timezone.utc) >= cutoff][-12:]
        except Exception:  # noqa: BLE001
            pass
        keep["_v"] = INFO_VERSION
        con.execute("INSERT OR REPLACE INTO stock_info VALUES(?,?,?)",
                    (t, json.dumps(keep), now.isoformat(timespec="seconds")))
        con.commit()
        n += 1
    return n


def _parse_news(t, raw):
    """yfinance vraća vesti u dva formata (stari i novi) - podrži oba."""
    out = []
    for n in raw or []:
        c = n.get("content") or n
        title = c.get("title")
        link = (c.get("canonicalUrl") or {}).get("url") or (c.get("clickThroughUrl") or {}).get("url") or c.get("link")
        if not title or not link:
            continue
        pub = c.get("pubDate") or c.get("displayTime")
        if not pub and c.get("providerPublishTime"):
            pub = datetime.fromtimestamp(c["providerPublishTime"], timezone.utc).isoformat()
        try:
            pub_dt = datetime.fromisoformat((pub or "").replace("Z", "+00:00"))
        except ValueError:
            pub_dt = datetime.now(timezone.utc)
        src = (c.get("provider") or {}).get("displayName") or c.get("publisher") or "Yahoo Finance"
        out.append({"id": hashlib.sha1(link.encode()).hexdigest()[:16], "source": src, "title": title.strip(),
                    "link": link, "summary": (c.get("summary") or c.get("description") or "")[:1500],
                    "published": pub_dt.astimezone(timezone.utc).isoformat(timespec="seconds"), "ticker": t})
    return out


def _gnews(t, name, n):
    """Vesti o kompaniji preko Google News pretrage (engleski, poslednjih 7 dana)."""
    import urllib.parse
    import feedparser
    import requests
    if n <= 0:
        return []
    q = urllib.parse.quote_plus(f'"{name}" (stock OR shares OR earnings OR company) when:7d')
    try:
        r = requests.get(f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en", timeout=15,
                         headers={"User-Agent": "Mozilla/5.0 FinNews/1.0"})
        feed = feedparser.parse(r.content)
    except Exception:  # noqa: BLE001
        return []
    out = []
    for e in feed.entries[:n]:
        src = (e.get("source") or {}).get("title") or "Google News"
        title = e.get("title") or ""
        if title.endswith(" - " + src):
            title = title[: -len(src) - 3]
        link = e.get("link")
        if not title or not link:
            continue
        try:
            pub = datetime(*e.published_parsed[:6], tzinfo=timezone.utc)
        except Exception:  # noqa: BLE001
            pub = datetime.now(timezone.utc)
        out.append({"id": hashlib.sha1(link.encode()).hexdigest()[:16], "source": src, "title": title.strip(), "link": link,
                    "summary": "", "published": pub.isoformat(timespec="seconds"), "ticker": t})
    return out


def refresh_news(con=None, per_ticker=8):
    import yfinance as yf
    con = con or db.connect()
    _init(con)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    new = 0
    import portfolio
    names = dict(watchlist())
    names.update(portfolio.names(con))
    for t in all_tickers(con):
        if t in ETFS or t == "EURUSD=X":
            continue
        try:
            items = _parse_news(t, yf.Ticker(t).news)[:per_ticker]
        except Exception:  # noqa: BLE001
            items = []
        if len(items) < 3 and "." in t:  # Yahoo često nema vesti za evropske firme - dopuni preko Google News-a
            items += _gnews(t, names.get(t, t), per_ticker - len(items))
        for it in items:
            cur = con.execute(
                "INSERT OR IGNORE INTO items(id, source, category, lang, title, link, summary, published, fetched_at, ticker) "
                "VALUES(?,?,?,?,?,?,?,?,?,?)",
                (it["id"], it["source"], "Kompanije", "en", it["title"], it["link"], it["summary"], it["published"], now, t))
            new += cur.rowcount
    con.commit()
    import fetcher
    fetcher.rescore(con)
    db.set_meta(con, "stock_news_refreshed", now)
    return new


# ---------- pokazatelji i predlog ----------
def series(con, t, days=None):
    _init(con)
    sql, args = "SELECT d, close FROM prices WHERE ticker=?", [t]
    if days:
        sql += " AND d >= ?"
        args.append((datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"))
    return [(r["d"], r["close"]) for r in con.execute(sql + " ORDER BY d", args)]


def _ret(closes, n):
    return closes[-1] / closes[-1 - n] - 1 if len(closes) > n and closes[-1 - n] else None


def metrics(con):
    _init(con)
    out = []
    infos = {r["ticker"]: json.loads(r["info"]) for r in con.execute("SELECT * FROM stock_info")}
    for t, name in watchlist():
        s = series(con, t)
        if len(s) < 30:
            continue
        c = [x[1] for x in s]
        rets = [c[i] / c[i - 1] - 1 for i in range(max(1, len(c) - 63), len(c))]
        mean = sum(rets) / len(rets)
        vol = math.sqrt(sum((r - mean) ** 2 for r in rets) / max(1, len(rets) - 1)) * math.sqrt(252)
        last252 = c[-252:]
        peak, mdd = last252[0], 0.0
        for v in last252:
            peak = max(peak, v)
            mdd = min(mdd, v / peak - 1)
        sma50 = sum(c[-50:]) / min(50, len(c))
        sma200 = sum(c[-200:]) / min(200, len(c))
        info = infos.get(t, {})
        tgt = info.get("targetMeanPrice")
        out.append({
            "ticker": t, "name": info.get("shortName") or name, "sector": info.get("sector") or ("ETF" if t in ETFS else ""),
            "currency": info.get("currency") or "", "price": c[-1], "date": s[-1][0],
            "r1d": _ret(c, 1), "r1w": _ret(c, 5), "r1m": _ret(c, 21), "r6m": _ret(c, 126), "r1y": _ret(c, 252),
            "mom": (c[-22] / c[-253] - 1) if len(c) > 253 else None,
            "vol": vol, "mdd": mdd, "sma50": sma50, "sma200": sma200, "spark": c[-90:],
            "pe": info.get("forwardPE") or info.get("trailingPE"), "peg": info.get("trailingPegRatio") or info.get("pegRatio"),
            "fpe": info.get("forwardPE"), "tpe": info.get("trailingPE"), "industry": info.get("industry") or "",
            "long_name": info.get("longName") or "", "ps": info.get("priceToSalesTrailing12Months"),
            "roe": info.get("returnOnEquity"), "margin": info.get("profitMargins"), "de": info.get("debtToEquity"),
            "growth": info.get("revenueGrowth"), "div": info.get("dividendYield"), "mcap": info.get("marketCap"), "fcf_yield": (info.get("freeCashflow") / info.get("marketCap")) if info.get("freeCashflow") is not None and info.get("marketCap") else None,
            "target": tgt, "upside": (tgt / c[-1] - 1) if tgt else None, "rec": info.get("recommendationMean"),
            "analysts": info.get("numberOfAnalystOpinions"), "summary": info.get("longBusinessSummary") or "",
            "etf": t in ETFS,
        })
    return out


FACTORS = [  # (ključ, težina, veće je bolje?, sr, en)
    ("mom", 0.25, True, "momentum (12-1 mesec)", "momentum (12-1 month)"),
    ("upside", 0.20, True, "potencijal do cilja analitičara", "upside to analyst target"),
    ("pe", 0.15, False, "vrednovanje (P/E)", "valuation (P/E)"),
    ("roe", 0.15, True, "profitabilnost (ROE)", "profitability (ROE)"),
    ("growth", 0.10, True, "rast prihoda", "revenue growth"),
    ("vol", 0.15, False, "niža volatilnost", "lower volatility"),
]


def _pct(values, v, higher):
    vals = sorted(x for x in values if x is not None)
    if v is None or not vals:
        return None
    rank = sum(1 for x in vals if x <= v) / len(vals)
    return rank if higher else 1 - rank + 1 / len(vals)


def score(rows):
    """Faktorski skor 0-100 unutar liste praćenja. Bez ETF-ova, P/E <= 0 se ne računa kao jeftino."""
    stocks = [r for r in rows if not r["etf"]]
    for r in stocks:
        if r["pe"] is not None and r["pe"] <= 0:
            r["pe"] = None
    for r in stocks:
        parts, wsum, tot = {}, 0.0, 0.0
        for k, w, hi, _, _ in FACTORS:
            p = _pct([x[k] for x in stocks], r[k], hi)
            if p is not None:
                parts[k] = p
                wsum += w
                tot += w * p
        trend = r["price"] > r["sma200"] and r["sma50"] > r["sma200"]
        base = tot / wsum if wsum else 0.5
        r["score"] = round(100 * (0.9 * base + 0.1 * (1 if trend else 0)))
        r["parts"] = parts
        r["trend"] = trend
    return sorted(stocks, key=lambda r: -r["score"])


def reasons(r, ui="sr"):
    """Kratko objašnjenje skora, iz brojeva."""
    sr = ui == "sr"
    out = []
    if r.get("mom") is not None:
        out.append((f"cena je za 12 meseci {'porasla' if r['mom'] >= 0 else 'pala'} {abs(r['mom']) * 100:.0f}%" if sr else
                    f"price {'up' if r['mom'] >= 0 else 'down'} {abs(r['mom']) * 100:.0f}% over 12 months"))
    if r.get("trend") is not None:
        out.append(("iznad dugoročnog proseka (200 dana)" if r["trend"] else "ispod dugoročnog trenda") if sr else
                   ("above the 200-day average" if r["trend"] else "below the long-term trend"))
    if r.get("pe"):
        out.append(f"P/E {r['pe']:.1f}")
    if r.get("roe") is not None:
        out.append(f"ROE {r['roe'] * 100:.0f}%")
    if r.get("upside") is not None:
        out.append((f"analitičari vide {r['upside'] * 100:+.0f}% do cilja" if sr else f"analysts see {r['upside'] * 100:+.0f}% to target"))
    if r.get("vol") is not None:
        out.append((f"volatilnost {r['vol'] * 100:.0f}% godišnje" if sr else f"volatility {r['vol'] * 100:.0f}% a year"))
    return out


def ai_view(r, news, ui):
    """Kratka analiza akcije (AI: Claude ili lokalni model)."""
    lines = "\n".join(f"- {n['title']} ({n['source']})" for n in news[:8]) or "-"
    nums = ", ".join(reasons(r, "en"))
    prompt = (f"Odgovori na: {ai._lang_instr(ui)}\n"
              f"Napiši kratku analizu akcije {r['name']} ({r['ticker']}) za investitora, u 4 kratka dela sa podnaslovima: "
              "**Šta se dešava** (iz vesti), **Brojevi** (iz pokazatelja), **Prilike**, **Rizici**. Najviše 150 reči. "
              "Koristi samo date podatke, bez izmišljanja. Na kraju jedna rečenica da ovo nije investicioni savet.\n\n"
              f"POKAZATELJI: {nums}; sektor {r['sector']}\nVESTI:\n{lines}")
    return ai._claude(prompt, ai.FAST_MODEL, 700)


def info(con, t):
    _init(con)
    row = con.execute("SELECT info FROM stock_info WHERE ticker=?", (t,)).fetchone()
    return json.loads(row["info"]) if row else {}


def apply_tax_preferences(ranked, con):
    """Dodaje informacije o regionu i porezu na dividendu. Skor se NE menja - sve akcije su ravnopravne."""
    import indicators
    for r in ranked:
        inf = info(con, r["ticker"])
        dy = indicators.values(inf, r)["div_y"]
        c = eu.country(r["ticker"], inf)
        r["region"] = eu.region(r["ticker"], inf)
        r["div_y"] = dy
        r["drag"] = eu.drag(dy, c)
        r["drag_reclaim"] = eu.drag(dy, c, reclaim=True)
        r["score_base"] = r["score"]
    return sorted(ranked, key=lambda r: -r["score"])


def market_strip(con):
    """Poslednja vrednost i dnevna promena za traku tržišta."""
    _init(con)
    out = []
    for t, name, dec in MARKETS:
        rows = con.execute("SELECT close FROM prices WHERE ticker=? ORDER BY d DESC LIMIT 2", (t,)).fetchall()
        if len(rows) == 2 and rows[1]["close"]:
            v = rows[0]["close"] / (10 if t == "^TNX" and rows[0]["close"] > 20 else 1)
            out.append((name, v, rows[0]["close"] / rows[1]["close"] - 1, dec))
    return out
