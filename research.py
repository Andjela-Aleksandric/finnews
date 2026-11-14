"""Naučni radovi preko OpenAlex-a (besplatna, otvorena baza ~250M radova, bez ključa).
Tri liste: najnovije iz top časopisa, najcitiranije u poslednjih 6/24 meseca, klasici oblasti."""
from datetime import date, datetime, timedelta, timezone

import requests

import ai
import db

API = "https://api.openalex.org/works"
TOP_JOURNALS = {
    "Journal of Finance": "0022-1082",
    "Journal of Financial Economics": "0304-405X",
    "Review of Financial Studies": "0893-9454",
    "Journal of Financial and Quantitative Analysis": "0022-1090",
    "Review of Finance": "1572-3097",
    "Journal of Banking & Finance": "0378-4266",
    "Financial Analysts Journal": "0015-198X",
    "Journal of Portfolio Management": "0095-4918",
    "Quantitative Finance": "1469-7688",
    "Expert Systems with Applications": "0957-4174",
    "Applied Soft Computing": "1568-4946",
}
DEFAULT_TOPICS = [
    "asset pricing", "portfolio optimization", "machine learning stock returns",
    "neural network financial forecasting", "fuzzy neural network stock market",
    "volatility forecasting", "market efficiency anomalies", "risk management finance",
    "behavioral finance", "cryptocurrency market", "monetary policy financial markets",
]
SELECT = ("id,doi,display_name,publication_date,publication_year,cited_by_count,"
          "authorships,primary_location,abstract_inverted_index,open_access,best_oa_location")
# Časopisi računarske inteligencije, prognoze i operacionih istraživanja - bitni za tvoju oblast
CI_JOURNALS = {
    "Expert Systems with Applications": "0957-4174", "Applied Soft Computing": "1568-4946",
    "Knowledge-Based Systems": "0950-7051", "IEEE Trans. Neural Networks and Learning Systems": "2162-237X",
    "IEEE Trans. Fuzzy Systems": "1063-6706", "Fuzzy Sets and Systems": "0165-0114",
    "European Journal of Operational Research": "0377-2217", "Decision Support Systems": "0167-9236",
    "Information Sciences": "0020-0255", "Neural Computing and Applications": "0941-0643",
    "Engineering Applications of AI": "0952-1976", "Financial Innovation": "2199-4730",
    "Finance Research Letters": "1544-6123", "International Review of Financial Analysis": "1057-5219",
    "Journal of Forecasting": "0277-6693", "International Journal of Forecasting": "0169-2070",
}
# Teme za doktorat - napredni nastavak master rada (LSTM + fazi profilisanje + MVO + objašnjivost)
PHD_TOPICS = [
    {"q": "LSTM deep learning stock return forecasting", "sr": "Duboko učenje (LSTM) za prognozu prinosa", "en": "Deep learning (LSTM) return forecasting"},
    {"q": "transformer time series financial forecasting", "sr": "Transformer modeli za finansijske serije", "en": "Transformers for financial time series"},
    {"q": "fuzzy inference investor risk profiling", "sr": "Fazi profilisanje rizika investitora", "en": "Fuzzy investor risk profiling"},
    {"q": "neuro-fuzzy ANFIS financial forecasting", "sr": "Neuro-fazi (ANFIS) u finansijama", "en": "Neuro-fuzzy (ANFIS) in finance"},
    {"q": "robo-advisor personalized portfolio recommendation", "sr": "Robo-savetnici i personalizovani portfolio", "en": "Robo-advisors & personalised portfolios"},
    {"q": "machine learning predictions portfolio optimization mean-variance", "sr": "ML prognoze u optimizaciji portfolija", "en": "ML forecasts in portfolio optimisation"},
    {"q": "naive diversification 1/N estimation error portfolio", "sr": "1/N vs. optimizacija i greška procene", "en": "1/N vs optimisation & estimation error"},
    {"q": "explainable artificial intelligence SHAP finance", "sr": "Objašnjiva veštačka inteligencija u finansijama", "en": "Explainable AI in finance"},
    {"q": "deep reinforcement learning portfolio management", "sr": "Učenje podsticanjem za upravljanje portfolijom", "en": "Deep RL for portfolio management"},
    {"q": "large language models investment decision making", "sr": "Veliki jezički modeli i investicione odluke", "en": "LLMs and investment decisions"},
] + [
    {"q": "decision-focused learning portfolio optimization", "sr": "Učenje usmereno na odluku (portfolio)", "en": "Decision-focused learning (portfolio)"},
    {"q": "predict-then-optimize portfolio estimation error", "sr": "Predvidi pa optimizuj i greška procene", "en": "Predict-then-optimise & estimation error"},
    {"q": "fuzzy robust portfolio optimization", "sr": "Fazi robusna optimizacija portfolija", "en": "Fuzzy robust portfolio optimisation"},
    {"q": "personalized portfolio optimization investor preferences", "sr": "Personalizovana optimizacija portfolija", "en": "Personalised portfolio optimisation"},
    {"q": "machine learning emerging frontier stock markets", "sr": "ML na tržištima u razvoju i graničnim tržištima", "en": "ML in emerging & frontier markets"},
    {"q": "conformal prediction financial forecasting", "sr": "Konformalna predikcija u finansijama", "en": "Conformal prediction in finance"},
]
# precizniji izrazi za brojanje radova (traže se u naslovu i abstraktu)
COUNT_EXPR = {
    "LSTM deep learning stock return forecasting": '"LSTM" AND ("stock" OR "return" OR "portfolio")',
    "transformer time series financial forecasting": '"transformer" AND ("stock" OR "financial" OR "portfolio")',
    "fuzzy inference investor risk profiling": '"fuzzy" AND ("investor" OR "risk tolerance" OR "risk profile")',
    "neuro-fuzzy ANFIS financial forecasting": '("ANFIS" OR "neuro-fuzzy") AND ("stock" OR "financial" OR "portfolio")',
    "robo-advisor personalized portfolio recommendation": '"robo-advisor" OR "robo-advisory" OR "robo advisor"',
    "machine learning predictions portfolio optimization mean-variance": '"machine learning" AND "portfolio optimization"',
    "naive diversification 1/N estimation error portfolio": '"naive diversification" OR ("estimation error" AND "portfolio")',
    "explainable artificial intelligence SHAP finance": '("explainable" OR "SHAP") AND ("finance" OR "financial" OR "stock" OR "credit")',
    "deep reinforcement learning portfolio management": '"reinforcement learning" AND "portfolio"',
    "large language models investment decision making": '("large language model" OR "LLM") AND ("investment" OR "stock" OR "portfolio")',
    "decision-focused learning portfolio optimization": '("decision-focused" OR "end-to-end") AND "portfolio"',
    "predict-then-optimize portfolio estimation error": '("predict-then-optimize" OR "smart predict") AND "portfolio"',
    "fuzzy robust portfolio optimization": '"fuzzy" AND "robust" AND "portfolio"',
    "personalized portfolio optimization investor preferences": '"personalized" AND "portfolio" AND ("investor" OR "preference")',
    "machine learning emerging frontier stock markets": '("machine learning" OR "deep learning") AND ("emerging market" OR "frontier market")',
    "conformal prediction financial forecasting": '"conformal prediction" AND ("financial" OR "stock" OR "portfolio")',
}
DEFAULT_THESIS = ("Master rad: Sistem za podršku finansijskom odlučivanju zasnovan na tehnikama računarske inteligencije. "
                  "Profilisanje investitora pomoću Mamdani fazi sistema (IBA agregacija ankete sa 588 ispitanika u "
                  "indikatore tolerancije rizika, finansijskog znanja i investicionog horizonta, K-Means granice, 27 "
                  "pravila), LSTM predviđanje prinosa ETF-ova (SPY, QQQ, SMH, GLD, AGG) sa statističkom validacijom "
                  "signala, Markowitz MVO optimizacija portfolija sa ciljanom volatilnošću po profilu i objašnjivost "
                  "(SHAP/LIME). Ključni nalaz: naivna 1/N diverzifikacija nadmašila je hibridni LSTM-MVO i istorijski MVO "
                  "(u skladu sa DeMiguel, Garlappi i Uppal, 2009). Ciljni korisnici: građani Srbije.")


def topics():
    return ai.load_config().get("research_topics") or DEFAULT_TOPICS


def _abstract(inv):
    if not inv:
        return ""
    pos = sorted((p, w) for w, ps in inv.items() for p in ps)
    return " ".join(w for _, w in pos)[:2500]


def _get(params):
    key = ai.load_config().get("openalex_api_key")
    if key:
        params["api_key"] = key
    params.setdefault("select", SELECT)
    r = requests.get(API, params=params, timeout=30,
                     headers={"User-Agent": "FinNews/1.0 (personal research reader)"})
    r.raise_for_status()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out = []
    for w in r.json().get("results", []):
        title = w.get("display_name")
        if not title:
            continue
        loc = w.get("primary_location") or {}
        src = (loc.get("source") or {}).get("display_name") or ""
        authors = [a.get("author", {}).get("display_name", "") for a in (w.get("authorships") or [])]
        best = w.get("best_oa_location") or {}
        out.append({
            "id": "oa_" + w["id"].rsplit("/", 1)[-1], "title": title,
            "authors": ", ".join(authors[:4]) + (" et al." if len(authors) > 4 else ""),
            "venue": src, "pub_date": w.get("publication_date") or "", "year": w.get("publication_year"),
            "cited_by": w.get("cited_by_count") or 0,
            "link": w.get("doi") or loc.get("landing_page_url") or w["id"],
            "abstract": _abstract(w.get("abstract_inverted_index")), "fetched_at": now,
            "pdf_url": best.get("pdf_url"), "oa": (w.get("open_access") or {}).get("is_oa", False),
        })
    return out


def _journals_filter():
    return "primary_location.source.issn:" + "|".join(TOP_JOURNALS.values())


def refresh(con=None, progress=None):
    con = con or db.connect()
    today = date.today()
    jobs = [("journals_new", {"filter": f"{_journals_filter()},from_publication_date:{(today - timedelta(days=120)).isoformat()}",
                              "sort": "publication_date:desc", "per-page": 100})]
    for months, tag in [(6, "cited_6m"), (24, "cited_24m")]:
        since = (today - timedelta(days=int(months * 30.5))).isoformat()
        jobs.append((tag, {"filter": f"{_journals_filter()},from_publication_date:{since}",
                           "sort": "cited_by_count:desc", "per-page": 60}))
        for t in topics():
            jobs.append((tag, {"search": t, "filter": f"from_publication_date:{since},type:article",
                               "sort": "cited_by_count:desc", "per-page": 8}))
    for t in topics():
        jobs.append(("classic", {"search": t, "filter": "type:article", "sort": "cited_by_count:desc",
                                 "per-page": 8}))
    seen_tags, errors = set(), 0
    for i, (tag, params) in enumerate(jobs, 1):
        try:
            papers = _get(params)
        except Exception:  # noqa: BLE001
            errors += 1
            continue
        if tag not in seen_tags:
            db.clear_tag(con, tag)
            seen_tags.add(tag)
        for p in papers:
            db.upsert_paper(con, p, tag)
        con.commit()
        if progress:
            progress(i / len(jobs))
    if errors < len(jobs):
        db.set_meta(con, "papers_refreshed", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    return {"jobs": len(jobs), "errors": errors}


# ---------- Doktorat radar ----------
def phd_topics():
    cfg = ai.load_config()
    custom = cfg.get("phd_topics")
    if custom and not cfg.get("phd_topics_v2"):  # dodaj nove teme i u ranije sačuvanu listu
        have = {tp["q"] for tp in custom}
        custom += [tp for tp in PHD_TOPICS if tp["q"] not in have]
        cfg.update({"phd_topics": custom, "phd_topics_v2": True})
        ai.save_config(cfg)
    return custom or PHD_TOPICS


def thesis_text():
    return ai.load_config().get("thesis_text") or DEFAULT_THESIS


def _count(params):
    params = dict(params, **{"per-page": 1, "select": "id"})
    key = ai.load_config().get("openalex_api_key")
    if key:
        params["api_key"] = key
    r = requests.get(API, params=params, timeout=30, headers={"User-Agent": "FinNews/1.0"})
    r.raise_for_status()
    return r.json().get("meta", {}).get("count", 0)


def refresh_phd(con=None, progress=None):
    """Najvažnije studije iz poslednjih 6 meseci po temama doktorata + trend (6m naspram prethodnih 6m)."""
    import math
    con = con or db.connect()
    today = date.today()
    d6 = (today - timedelta(days=183)).isoformat()
    d12 = (today - timedelta(days=366)).isoformat()
    venues = set(TOP_JOURNALS) | set(CI_JOURNALS)
    topics = phd_topics()
    errors, steps = 0, len(topics) * 4
    con.execute("DELETE FROM phd")
    for i, tp in enumerate(topics):
        q = tp["q"]
        found = {}
        for j, params in enumerate([
            {"search": q, "filter": f"from_publication_date:{d6},type:article|preprint", "per-page": 25},
            {"search": q, "filter": f"from_publication_date:{d6},type:article|preprint", "sort": "cited_by_count:desc", "per-page": 15},
            {"search": q, "filter": f"from_publication_date:{(today - timedelta(days=731)).isoformat()},to_publication_date:{d6},type:article|preprint", "sort": "cited_by_count:desc", "per-page": 15},
        ]):
            try:
                for rank, p in enumerate(_get(params)):
                    rel = 1 - rank / 25 if j == 0 else 0.5 if j == 1 else 0.35
                    found.setdefault(p["id"], (p, 0))
                    found[p["id"]] = (p, max(found[p["id"]][1], rel))
            except Exception:  # noqa: BLE001
                errors += 1
            if progress:
                progress((i * 4 + j + 1) / steps)
        for pid, (p, rel) in found.items():
            try:
                age = max(1, (today - date.fromisoformat(p["pub_date"])).days)
            except ValueError:
                age = 120
            score = (1.6 * rel + math.log1p(p["cited_by"]) / math.log1p(40) + (0.7 if p["venue"] in venues else 0)
                     + (0.3 if p.get("oa") else 0) + 0.4 * max(0, 1 - age / 183) + (0.2 if p["abstract"] else -0.5))
            db.upsert_paper(con, p, "phd")
            con.execute("INSERT OR REPLACE INTO phd VALUES(?,?,?)", (pid, q, round(score, 3)))
        try:  # OpenAlex kasni sa unosom najnovijih radova, pa se rast meri na „zrelim“ periodima
            expr = COUNT_EXPR.get(q, q)
            f6 = f"title_and_abstract.search:{expr}"
            recent = _count({"filter": f"{f6},from_publication_date:{d6}"})
            a3 = (today - timedelta(days=91)).isoformat(); a9 = (today - timedelta(days=274)).isoformat()
            a15 = (today - timedelta(days=457)).isoformat()
            g_new = _count({"filter": f"{f6},from_publication_date:{a9},to_publication_date:{a3}"})
            g_old = _count({"filter": f"{f6},from_publication_date:{a15},to_publication_date:{a9}"})
            con.execute("INSERT OR REPLACE INTO phd_trends VALUES(?,?,?,?)",
                        (q, recent, g_old if g_new else 0, datetime.now(timezone.utc).isoformat(timespec="seconds")))
            con.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", (f"trend_new_{q}", str(g_new)))
        except Exception:  # noqa: BLE001
            errors += 1
        con.commit()
        if progress:
            progress((i * 4 + 4) / steps)
    if errors < steps:
        db.set_meta(con, "phd_refreshed", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    return {"steps": steps, "errors": errors}


TOPIC_PERIODS = (1, 3, 6, 12, 24)


def refresh_topic_counts(con=None, max_age_days=7):
    """Broj radova po temi u OpenAlex-u za poslednjih 1, 3, 6, 12 i 24 meseca i za prethodni period iste dužine.
    Jedan zapis po temi u meta tabeli: topic_counts_<tema> = {"1": [sada, pre], ...}."""
    import json
    con = con or db.connect()
    last = db.get_meta(con, "topic_counts_refreshed")
    if last and datetime.now(timezone.utc) - datetime.fromisoformat(last) < timedelta(days=max_age_days):
        return {"skipped": True}
    today = date.today()
    ok = errors = 0
    for tp in phd_topics():
        q = tp["q"]
        f = f"title_and_abstract.search:{COUNT_EXPR.get(q, q)}"
        out = {}
        for m in TOPIC_PERIODS:
            a = (today - timedelta(days=round(30.44 * m))).isoformat()
            b = (today - timedelta(days=round(30.44 * 2 * m))).isoformat()
            try:
                now_n = _count({"filter": f"{f},from_publication_date:{a}"})
                prev_n = _count({"filter": f"{f},from_publication_date:{b},to_publication_date:{a}"})
                out[str(m)] = [now_n, prev_n]
                ok += 1
            except Exception:  # noqa: BLE001
                errors += 1
        if out:
            db.set_meta(con, f"topic_counts_{q}", json.dumps(out))
    if ok:
        db.set_meta(con, "topic_counts_refreshed", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    return {"ok": ok, "errors": errors}


def refresh_gaps(con=None, progress=None):
    """Mapa praznina: broj radova u finansijama za svaku kombinaciju metod x problem (poslednje 2 godine)."""
    import insights
    con = con or db.connect()
    con.execute("CREATE TABLE IF NOT EXISTS gap_map(mi INTEGER, pi INTEGER, cnt INTEGER, PRIMARY KEY(mi, pi))")
    since = (date.today() - timedelta(days=730)).isoformat()
    n = len(insights.GAP_METHODS) * len(insights.GAP_PROBLEMS)
    k = errors = 0
    for mi, m in enumerate(insights.GAP_METHODS):
        for pi, p in enumerate(insights.GAP_PROBLEMS):
            k += 1
            try:
                c = _count({"filter": f"title_and_abstract.search:({m[2]}) AND ({p[2]}),from_publication_date:{since}"})
                con.execute("INSERT OR REPLACE INTO gap_map VALUES(?,?,?)", (mi, pi, c))
            except Exception:  # noqa: BLE001
                errors += 1
            if progress:
                progress(k / n)
    con.commit()
    if errors < n:
        db.set_meta(con, "gaps_refreshed", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    return {"steps": n, "errors": errors}


def gap_cells(con):
    try:
        return {(r["mi"], r["pi"]): r["cnt"] for r in con.execute("SELECT * FROM gap_map")}
    except Exception:  # noqa: BLE001
        return {}
