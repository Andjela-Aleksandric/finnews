"""Prilike na tržištu: akcije koje su pale, a za koje podaci i vesti ukazuju na mogući oporavak,
i teme iz vesti koje se zahuktavaju (sa sektorima na koje mogu da utiču).

Sve je pravilo koje se može proveriti (bez AI modela) - služi za istraživanje, a ne kao investicioni savet."""
import math
import re
from datetime import datetime, timedelta, timezone

import db
import stocks

SECTOR_SR = {"Technology": "Tehnologija", "Healthcare": "Zdravstvo", "Financial Services": "Finansije",
             "Consumer Cyclical": "Ciklična potrošnja", "Consumer Defensive": "Osnovna potrošnja", "Industrials": "Industrija",
             "Energy": "Energetika", "Utilities": "Komunalne usluge", "Real Estate": "Nekretnine",
             "Basic Materials": "Sirovine", "Communication Services": "Komunikacije"}

POS = {"beat": 2, "beats": 2, "tops estimates": 2, "raises guidance": 3, "raised guidance": 3, "lifts outlook": 3, "raises outlook": 3,
       "record": 1, "upgrade": 2, "upgraded": 2, "buyback": 2, "share repurchase": 2, "approval": 2, "approved": 1,
       "wins contract": 2, "contract": 1, "partnership": 1, "rebound": 1, "rallies": 1, "surges": 1, "jumps": 1, "soars": 1,
       "strong demand": 2, "outperform": 2, "overweight": 1, "dividend increase": 2, "raises dividend": 2, "expands": 1,
       "acquisition": 1, "breakthrough": 2, "profit rises": 2, "revenue rises": 1, "better-than-expected": 2, "better than expected": 2}
NEG = {"miss": 2, "misses": 2, "cuts guidance": 3, "lowers guidance": 3, "cuts outlook": 3, "warns": 2, "profit warning": 3,
       "downgrade": 2, "downgraded": 2, "probe": 2, "investigation": 2, "lawsuit": 2, "fine": 1, "fined": 2, "recall": 2,
       "layoffs": 1, "job cuts": 1, "plunges": 2, "slumps": 2, "tumbles": 2, "falls": 1, "drops": 1, "sinks": 1,
       "fraud": 3, "antitrust": 2, "ban": 1, "weak demand": 2, "underperform": 2, "underweight": 1, "worse-than-expected": 2,
       "worse than expected": 2, "delay": 1, "halts": 2, "default": 2, "strike": 1}

# (ključ, sr, en, regex, {sektor: smer}, objašnjenje sr, objašnjenje en)
THEMES = [
    ("cuts", "Smanjenje kamata", "Rate cuts", r"rate cut|cuts? (interest )?rates|cutting rates|easing cycle|dovish|lower borrowing costs",
     {"Technology": 1, "Real Estate": 1, "Utilities": 1, "Consumer Cyclical": 1, "Financial Services": -0.5},
     "Niže kamate obično pomažu kompanijama čija se vrednost zasniva na budućem rastu i sektorima sa mnogo duga (nekretnine, komunalije).",
     "Lower rates usually help growth companies and debt-heavy sectors (real estate, utilities)."),
    ("hot_inflation", "Inflacija sporo popušta", "Sticky inflation", r"hotter.than.expected|inflation (rises|jumps|accelerates|surges|picks up)|sticky inflation|rate hike|hawkish",
     {"Technology": -1, "Real Estate": -1, "Utilities": -0.5, "Financial Services": 0.5, "Energy": 0.5},
     "Viša inflacija znači duže visoke kamate - pritisak na skupe rastuće akcije, korist za banke.",
     "Higher inflation means rates stay high for longer - pressure on expensive growth stocks, support for banks."),
    ("ai", "AI i čipovi", "AI & chips", r"\bai\b|artificial intelligence|data cent(er|re)|\bgpu|chip demand|semiconductor|nvidia|hyperscaler",
     {"Technology": 1, "Communication Services": 0.7, "Utilities": 0.5, "Industrials": 0.3},
     "Ulaganja u AI povećavaju potražnju za čipovima, data centrima i strujom.",
     "AI spending lifts demand for chips, data centres and electricity."),
    ("oil_up", "Rast cene nafte", "Oil rising", r"(oil|crude|brent)( prices?)? (rises|rise|jumps|surges|climbs|rallies|spikes)|opec\+? (cut|output cut)",
     {"Energy": 1, "Industrials": -0.5, "Consumer Cyclical": -0.5},
     "Skuplja nafta pomaže naftnim kompanijama, a poskupljuje transport i proizvodnju.",
     "Pricier oil helps oil companies and raises costs for transport and manufacturing."),
    ("oil_down", "Pad cene nafte", "Oil falling", r"(oil|crude|brent)( prices?)? (falls|fall|drops|slides|slumps|tumbles|plunges)",
     {"Energy": -1, "Consumer Cyclical": 0.5, "Industrials": 0.5},
     "Jeftinija nafta smanjuje troškove potrošačima i industriji, a pritiska naftne kompanije.",
     "Cheaper oil lowers costs for consumers and industry and weighs on oil companies."),
    ("tariffs", "Carine i trgovinski sporovi", "Tariffs & trade", r"tariff|trade war|export control|trade tension|sanction",
     {"Industrials": -0.7, "Consumer Cyclical": -0.7, "Technology": -0.5, "Basic Materials": -0.3},
     "Carine poskupljuju uvoz i lance snabdevanja - najviše trpe izvoznici i proizvođači.",
     "Tariffs raise import and supply-chain costs - exporters and manufacturers suffer most."),
    ("defense", "Odbrana i naoružanje", "Defence spending", r"defen[cs]e (spending|budget|stocks)|military spending|rearm|nato (spending|target)",
     {"Industrials": 1},
     "Veći vojni budžeti u Evropi direktno povećavaju porudžbine odbrambenoj industriji.",
     "Higher military budgets in Europe directly lift orders for defence companies."),
    ("china", "Podsticaji u Kini", "China stimulus", r"china.{0,40}(stimulus|support measures|rate cut)|pboc (cut|eases)|beijing.{0,30}stimulus",
     {"Basic Materials": 1, "Consumer Cyclical": 0.7, "Industrials": 0.5},
     "Kineski podsticaji povećavaju potražnju za sirovinama i luksuznom robom (važno za evropske kompanije).",
     "Chinese stimulus lifts demand for raw materials and luxury goods (important for European companies)."),
    ("slowdown", "Strah od usporavanja", "Slowdown fears", r"recession|economic slowdown|growth slows|jobless claims (rise|jump)|weak jobs|layoffs (rise|surge)",
     {"Consumer Defensive": 1, "Healthcare": 0.7, "Utilities": 0.7, "Consumer Cyclical": -1, "Industrials": -0.7},
     "U usporavanju investitori prelaze u stabilne sektore (osnovna potrošnja, zdravstvo, komunalije).",
     "In a slowdown investors rotate into defensive sectors (staples, healthcare, utilities)."),
    ("health", "Lekovi i odobrenja", "Drugs & approvals", r"fda approv|\bema\b.{0,20}approv|glp-1|obesity drug|weight.loss drug|clinical trial",
     {"Healthcare": 1},
     "Odobrenja lekova i rezultati studija pokreću farmaceutske akcije.",
     "Drug approvals and trial results move pharmaceutical stocks."),
    ("banks", "Banke i krediti", "Banks & lending", r"net interest income|bank earnings|loan growth|bank profits?|lenders?",
     {"Financial Services": 0.8},
     "Rezultati banaka i kreditna aktivnost pokreću finansijski sektor.",
     "Bank results and lending activity drive the financial sector."),
]


def sentiment(text):
    """Jednostavan rečnik pozitivnih i negativnih izraza (finansijske vesti, engleski)."""
    t = " " + (text or "").lower() + " "
    p = sum(w for k, w in POS.items() if re.search(r"\b" + re.escape(k) + r"\b", t))
    n = sum(w for k, w in NEG.items() if re.search(r"\b" + re.escape(k) + r"\b", t))
    return p - n


def _iso(days):
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat(timespec="seconds")


def theme_momentum(con, days=7):
    """Koliko se o svakoj temi piše u poslednjih `days` dana u odnosu na prosek prethodna 4 perioda iste dužine."""
    rows = [dict(r) for r in con.execute(
        "SELECT id, title, summary, source, link, published, score FROM items WHERE published >= ? AND category != 'Istraživanja'",
        (_iso(days * 5),))]
    cut = _iso(days)
    out = []
    for key, sr, en, rx, eff, xs, xe in THEMES:
        r_ = re.compile(rx, re.I)
        hits = [x for x in rows if r_.search(x["title"] + " " + (x["summary"] or "")[:300])]
        now = [x for x in hits if x["published"] >= cut]
        before = (len(hits) - len(now)) / 4
        if len(now) < 2:
            continue
        ratio = (len(now) + 1) / (before + 1)
        now.sort(key=lambda x: -(x["score"] or 0))
        out.append({"key": key, "sr": sr, "en": en, "n": len(now), "prev": before, "ratio": ratio,
                    "heat": len(now) * min(ratio, 3) ** 0.5, "effects": eff, "why_sr": xs, "why_en": xe, "items": now[:4]})
    out.sort(key=lambda x: -x["heat"])
    return out


def sector_tailwind(themes):
    """Zbir uticaja tema na svaki sektor (normalizovano -1..1)."""
    if not themes:
        return {}
    mx = max(t["heat"] for t in themes) or 1
    tw = {}
    for t in themes:
        for sec, sign in t["effects"].items():
            tw[sec] = tw.get(sec, 0) + sign * t["heat"] / mx
    return {k: max(-1.0, min(1.0, v / 1.5)) for k, v in tw.items()}


def _rsi(c, n=14):
    if len(c) <= n:
        return None
    gains = losses = 0.0
    for i in range(len(c) - n, len(c)):
        d = c[i] - c[i - 1]
        gains += max(d, 0)
        losses += max(-d, 0)
    if losses == 0:
        return 100.0
    rs = gains / losses
    return 100 - 100 / (1 + rs)


def company_news(con, ticker, name, days=21):
    first = (name or "").split(" ")[0]
    q = ("SELECT id, title, summary, source, link, published, lang, category, score FROM items WHERE published >= ? "
         "AND (ticker = ? OR (length(?) > 3 AND title LIKE ?)) ORDER BY published DESC LIMIT 40")
    return [dict(r) for r in con.execute(q, (_iso(days), ticker, first, f"%{first}%"))]


def _clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def _sma(c, n):
    return sum(c[-n:]) / min(n, len(c)) if c else None


def setup_of(c, rsi, rsi_prev):
    """Faza trenda po pravilima iz vodiča: SMA 200 kaže pravac, RSI kaže gde smo u pokretu."""
    s50, s200 = _sma(c, 50), _sma(c, 200)
    s50p, s200p = _sma(c[:-10], 50), _sma(c[:-10], 200)
    above200 = c[-1] > s200
    golden = s50 > s200 and s50p <= s200p
    death = s50 < s200 and s50p >= s200p
    turning = rsi is not None and rsi_prev is not None and rsi > rsi_prev
    if above200 and rsi is not None and 30 <= rsi <= 50 and turning:
        kind, val = "pullback", 1.0      # povlačenje u rastućem trendu - najbolji ulaz
    elif above200 and rsi is not None and rsi > 70:
        kind, val = "hot", 0.25          # prekupljeno - sačekati
    elif above200:
        kind, val = "uptrend", 0.75
    elif c[-1] > s50 and turning:
        kind, val = "recovery", 0.55     # ispod 200, ali se vraća iznad 50-dnevnog proseka
    elif rsi is not None and rsi < 30 and not turning:
        kind, val = "knife", 0.05        # strm pad koji se nastavlja - čekati
    else:
        kind, val = "downtrend", 0.25
    return {"kind": kind, "val": val, "above200": above200, "golden": golden, "death": death, "s50": s50, "s200": s200}


def opportunities(con, rows, themes=None):
    """Akcije u padu za koje analitičari, kvalitet, vrednovanje, trend, vesti i teme ukazuju na mogući rast.
    Principi: kupuj kvalitet na popustu, ali u zdravom trendu (iznad 200-dnevnog proseka), ulaz pri RSI 30-50,
    vrednovanje kroz forward P/E i PEG u odnosu na rast, sektor kome aktuelne vesti idu na ruku."""
    themes = themes if themes is not None else theme_momentum(con, 7)
    tw = sector_tailwind(themes)
    out = []
    for r in rows:
        if r.get("etf"):
            continue
        s = stocks.series(con, r["ticker"], days=380)
        c = [x[1] for x in s]
        if len(c) < 60:
            continue
        hi = max(c[-252:])
        dd = c[-1] / hi - 1
        rsi = _rsi(c)
        rsi_prev = _rsi(c[:-5])
        st = setup_of(c, rsi, rsi_prev)
        news = company_news(con, r["ticker"], r["name"])
        sents = [(sentiment(n["title"] + " " + (n["summary"] or "")[:300]), n) for n in news]
        sent = sum(x for x, _ in sents)
        upside, rec, sec = r.get("upside"), r.get("rec"), r.get("sector") or ""
        tail = tw.get(sec, 0.0)
        growth, fpe, peg, margin = r.get("growth"), r.get("fpe"), r.get("peg"), r.get("margin")
        fcf_yield = r.get("fcf_yield")

        disc = _clamp(-dd / 0.40) if dd < 0 else 0.0
        ups = _clamp((upside or 0) / 0.40)
        q_parts = [x for x in (
            _clamp((r["roe"] or 0) / 0.25) if r.get("roe") is not None else None,
            _clamp((margin or 0) / 0.20) if margin is not None else None,
            _clamp(((growth or 0) + 0.05) / 0.35) if growth is not None else None,
            _clamp((fcf_yield + 0.02) / 0.10) if fcf_yield is not None else None) if x is not None]
        qual = sum(q_parts) / len(q_parts) if q_parts else 0.5
        if peg:
            val = 1.0 if peg < 1 else 0.7 if peg < 1.5 else 0.45 if peg < 2 else 0.15
        elif fpe:
            val = 1.0 if fpe < 15 else 0.75 if fpe < 22 else 0.5 if fpe < 30 else 0.2
        else:
            val = 0.4
        if fcf_yield is not None:
            fcf_score = _clamp((fcf_yield + 0.02) / 0.07)
            val = 0.75 * val + 0.25 * fcf_score
        if fpe and growth and growth > 0.25 and fpe < 45:
            val = max(val, 0.7)  # brz rast opravdava višu cenu
        recs = _clamp((3.5 - rec) / 2.5) if rec else 0.5
        news_s = 0.5 + 0.5 * math.tanh(sent / 4) if news else 0.5
        sect = 0.5 + 0.5 * tail
        score = 100 * (0.20 * disc + 0.17 * ups + 0.12 * qual + 0.12 * val + 0.08 * recs + 0.09 * news_s + 0.14 * st["val"] + 0.08 * sect)

        if st["kind"] == "knife":
            score *= 0.75  # vodič: ne kupovati dok pad ne uspori
        elif st["kind"] == "hot":
            score *= 0.85
        qualifies = bool(dd <= -0.08 and ((upside or 0) >= 0.05 or (rec is not None and rec <= 2.3)) and (rec is None or rec <= 3.0))
        reasons, risks = [("dd", dd)], []
        if upside:
            reasons.append(("upside", upside))
        if rec:
            reasons.append(("rec", rec))
        if r.get("roe") and r["roe"] > 0.15:
            reasons.append(("roe", r["roe"]))
        if growth and growth > 0.05:
            reasons.append(("growth", growth))
        if fcf_yield is not None:
            reasons.append(("fcf", fcf_yield))
        if peg and peg < 1.5:
            reasons.append(("peg", peg))
        elif fpe and fpe < 20:
            reasons.append(("fpe", fpe))
        if st["kind"] == "pullback":
            reasons.append(("pullback", rsi))
        elif st["kind"] == "recovery":
            reasons.append(("turning", None))
        if st["golden"]:
            reasons.append(("golden", None))
        if tail > 0.15:
            reasons.append(("tail", tail))
        if not st["above200"]:
            risks.append(("below200", None))
        if st["kind"] == "knife":
            risks.append(("knife", rsi))
        if st["kind"] == "hot":
            risks.append(("hot", rsi))
        if st["death"]:
            risks.append(("death", None))
        if sent < -1:
            risks.append(("neg_news", sent))
        if r.get("vol") and r["vol"] > 0.45:
            risks.append(("vol", r["vol"]))
        if (peg and peg > 2.5) or (fpe and fpe > 45):
            risks.append(("pe", fpe or r.get("pe")))
        if growth is not None and growth < 0:
            risks.append(("shrink", growth))
        if tail < -0.15:
            risks.append(("headwind", tail))
        if r.get("de") and r["de"] > 200:
            risks.append(("debt", r["de"]))
        checklist = [
            ("trend", st["above200"]), ("rsi", rsi is not None and 30 <= rsi <= 55),
            ("growth", None if growth is None else growth > 0.10), ("profit", None if margin is None else margin > 0),
            ("value", None if not (peg or fpe or fcf_yield is not None) else bool((peg and peg < 2) or (not peg and fpe and fpe < 30) or (fcf_yield is not None and fcf_yield >= 0.03))),
            ("debt", None if r.get("de") is None else r["de"] < 150), ("sector", tail > 0.05 if tail else None),
            ("news", None if not news else sent >= 0), ("analysts", None if upside is None else upside >= 0.10)]
        cat = sorted([x for x in sents if x[0] > 0], key=lambda x: (-x[0], x[1]["published"]))[:3]
        neg = sorted([x for x in sents if x[0] < 0], key=lambda x: x[0])[:2]
        th = [t for t in themes if t["effects"].get(sec)]
        out.append(dict(r, dd=dd, hi=hi, rsi=rsi, sent=sent, n_news=len(news), tail=tail, opp=round(score), qualifies=qualifies,
                        setup=st["kind"], above200=st["above200"], golden=st["golden"], death=st["death"],
                        reasons=reasons, risks=risks, checklist=checklist, catalysts=[n for _, n in cat], negatives=[n for _, n in neg],
                        themes=[(t["sr"], t["en"], t["effects"][sec]) for t in th[:3]],
                        parts={"disc": disc, "ups": ups, "qual": qual, "val": val, "recs": recs, "news": news_s, "tech": st["val"], "sect": sect}))
    out.sort(key=lambda x: (-x["qualifies"], -x["opp"]))
    return out


SETUP_TXT = {
    "pullback": ("Kratka korekcija u rastućem trendu - često dobar trenutak za kupovinu", "A pullback inside an uptrend - often a good entry point"),
    "uptrend": ("Rastući trend - cena je iznad proseka od 200 dana", "Uptrend - the price is above its 200-day average"),
    "hot": ("Prekupljena (RSI iznad 70) - prebrzo je porasla, bolje sačekati korekciju", "Overheated (RSI above 70) - better to wait for a pullback"),
    "recovery": ("Moguć početak oporavka - cena je još ispod proseka od 200 dana", "A recovery may be starting - still below the 200-day average"),
    "downtrend": ("Opadajući trend - sačekaj znak da se okreće", "Downtrend - wait for a sign that it is turning"),
    "knife": ("Pad se nastavlja - preprodata je, ali još nema znaka da se zaustavlja", "Falling knife - oversold, but still dropping"),
}
CHECK_TXT = {
    "trend": ("Cena je iznad proseka od 200 dana", "Price is above the 200-day average"),
    "rsi": ("RSI je u zoni za ulaz (30-55)", "RSI is in the entry zone (30-55)"),
    "growth": ("Prihodi rastu više od 10% godišnje", "Revenue is growing more than 10% a year"),
    "profit": ("Kompanija posluje sa dobitkom", "The company is profitable"),
    "value": ("Cena je razumna (PEG ispod 2 ili očekivani P/E ispod 30)", "Fair price (PEG under 2 or forward P/E under 30)"),
    "debt": ("Dug je pod kontrolom", "Debt is under control"),
    "sector": ("Vesti idu na ruku sektoru", "The news is a tailwind for the sector"),
    "news": ("Vesti o kompaniji nisu negativne", "Company news isn't negative"),
    "analysts": ("Analitičari očekuju rast od bar 10%", "Analysts expect at least 10% upside"),
}
TIER_SIZE = {"core": ("do ~10% portfolija - za držanje godinama", "up to ~10% of the portfolio - one to hold for years"),
             "growth": ("1-5% portfolija - proveri je svakog kvartala", "1-5% of the portfolio - re-check it every quarter"),
             "spec": ("manje od 1% portfolija - može i da propadne", "under 1% of the portfolio - it could fail")}

REASON_TXT = {
    "dd": ("{:.0f}% ispod najviše cene u poslednjih godinu dana", "{:.0f}% below its 52-week high", lambda v: abs(v) * 100),
    "upside": ("analitičari očekuju još {:+.0f}% do ciljne cene", "analysts see {:+.0f}% upside to their target", lambda v: v * 100),
    "rec": ("prosečna preporuka analitičara je {:.1f} (1 = kupi, 5 = prodaj)", "average analyst rating is {:.1f} (1 = buy, 5 = sell)", lambda v: v),
    "roe": ("veoma profitabilna - ROE {:.0f}%", "highly profitable - ROE {:.0f}%", lambda v: v * 100),
    "growth": ("prihodi rastu {:.0f}% godišnje", "revenue is up {:.0f}% year over year", lambda v: v * 100),
    "fcf": ("dobro zarađuje gotovinu - slobodan novčani tok je {:.1f}% tržišne vrednosti", "strong cash generation - free cash flow yield of {:.1f}%", lambda v: v * 100),
    "turning": ("cena se vratila iznad proseka od 20 dana - moguć početak oporavka", "back above its 20-day average - a recovery may be starting", None),
    "oversold": ("RSI {:.0f} - preprodata, pritisak prodaje možda slabi", "RSI {:.0f} - oversold, sellers may be running out of steam", lambda v: v),
    "tail": ("aktuelne vesti idu na ruku celom sektoru", "current news is a tailwind for the whole sector", None),
    "peg": ("PEG {:.1f} - cena je razumna s obzirom na rast", "PEG {:.1f} - a fair price for the growth", lambda v: v),
    "fpe": ("očekivani P/E {:.0f} - skromno vrednovana", "forward P/E {:.0f} - a modest valuation", lambda v: v),
    "pullback": ("RSI {:.0f} u rastućem trendu - privremeni pad, a ne promena trenda", "RSI {:.0f} in an uptrend - a healthy pullback, not a breakdown", lambda v: v),
    "golden": ("prosek od 50 dana upravo je prešao iznad proseka od 200 dana - trend se okreće naviše", "golden cross - the 50-day average crossed above the 200-day", None),
}
RISK_TXT = {
    "below200": ("cena je i dalje ispod proseka od 200 dana - dugoročni trend se još nije okrenuo", "still below its 200-day average - the long-term trend hasn't turned yet", None),
    "neg_news": ("u vestima je trenutno više loših nego dobrih informacija", "recent news has been mostly negative", None),
    "vol": ("cena jako oscilira ({:.0f}% godišnje)", "big price swings ({:.0f}% a year)", lambda v: v * 100),
    "pe": ("skupa u odnosu na zaradu (P/E {:.0f})", "pricey relative to earnings (P/E {:.0f})", lambda v: v),
    "headwind": ("aktuelne vesti ne idu na ruku sektoru", "current news themes are a headwind for the sector", None),
    "debt": ("visok dug (D/E {:.0f}%)", "high debt (D/E {:.0f}%)", lambda v: v),
    "knife": ("RSI {:.0f}, a pad se i dalje ubrzava - sačekaj da se cena smiri pre kupovine", "RSI {:.0f} and still falling - don't catch a falling knife", lambda v: v),
    "hot": ("RSI {:.0f} - prekupljena, ne kupuj dok cena naglo raste", "RSI {:.0f} - overheated, don't chase it", lambda v: v),
    "death": ("prosek od 50 dana pao je ispod proseka od 200 dana - trend se okreće naniže", "death cross - the 50-day average fell below the 200-day", None),
    "shrink": ("prihodi padaju ({:.0f}%)", "revenue is shrinking ({:.0f}%)", lambda v: v * 100),
}


def text(code, val, ui, table):
    sr, en, f = table[code]
    tpl = sr if ui == "sr" else en
    out = tpl.format(f(val)) if f and val is not None else tpl
    if ui == "sr":  # decimalni zarez na srpskom: 11,7% a ne 11.7%
        import re
        out = re.sub(r"(\d)\.(\d)", r"\1,\2", out)
    return out
