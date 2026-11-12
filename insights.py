"""Analiza studija bez AI: prepoznavanje metoda, podataka, rezultata i ograničenja iz teksta,
zbirni pregled oblasti i mapa praznina (metod x problem)."""
import re
from collections import Counter

import reader

METHODS = [  # (sr, en, regex)
    ("LSTM / GRU", "LSTM / GRU", r"\blstm\b|\bgru\b|long short-term memory"),
    ("Transformer", "Transformer", r"transformer|attention mechanism|\bbert\b"),
    ("Veliki jezički modeli", "Large language models", r"large language model|\bllms?\b|gpt|chatgpt"),
    ("Učenje podsticanjem", "Reinforcement learning", r"reinforcement learning|\bdrl\b|\bppo\b|q-learning"),
    ("Fazi logika", "Fuzzy logic", r"fuzzy"),
    ("ANFIS / neuro-fazi", "ANFIS / neuro-fuzzy", r"anfis|neuro-fuzzy|neurofuzzy"),
    ("Stabla i boosting", "Trees & boosting", r"random forest|xgboost|lightgbm|gradient boosting|catboost"),
    ("GARCH / ekonometrija", "GARCH / econometrics", r"garch|\barima\b|\bvar model|cointegration"),
    ("Grafovske neuronske mreže", "Graph neural networks", r"graph neural|\bgnn\b|graph convolution"),
    ("Objašnjiva AI (SHAP/LIME)", "Explainable AI (SHAP/LIME)", r"\bshap\b|\blime\b|explainab|interpretab"),
    ("Genetski / evolutivni algoritmi", "Genetic / evolutionary", r"genetic algorithm|evolutionary|particle swarm|\bpso\b"),
    ("Bajesovske metode", "Bayesian methods", r"bayesian"),
    ("Konformalna predikcija", "Conformal prediction", r"conformal"),
    ("Optimizacija (MVO, robusna)", "Optimisation (MVO, robust)", r"mean-variance|markowitz|robust optimi|risk parity|black-litterman"),
]
DATA = [
    ("Američke akcije (S&P 500, NASDAQ)", "US equities (S&P 500, NASDAQ)", r"s&p ?500|nasdaq|dow jones|u\.s\. stock|us stock|crsp"),
    ("Kina", "China", r"china|chinese|csi ?300|shanghai|shenzhen"),
    ("Kriptovalute", "Crypto", r"bitcoin|crypto|ethereum"),
    ("Devizno tržište", "FX", r"exchange rate|forex|\bfx\b|currency"),
    ("ETF-ovi i fondovi", "ETFs & funds", r"\betfs?\b|mutual fund|index fund"),
    ("Tržišta u razvoju", "Emerging markets", r"emerging market|frontier market|developing countr"),
    ("Evropa", "Europe", r"europe|euro stoxx|\bdax\b|ftse"),
    ("Indija", "India", r"india|nifty|sensex"),
    ("Vesti i tekst (sentiment)", "News & text (sentiment)", r"sentiment|news|twitter|textual"),
    ("Ankete i investitori", "Surveys & investors", r"survey|questionnaire|respondent|retail investor"),
]


def _hits(text, table, ui):
    low = (text or "").lower()
    return [(sr if ui == "sr" else en) for sr, en, rx in table if re.search(rx, low)]


def analyze(abstract, conclusion, ui="sr"):
    text = (abstract or "") + " " + (conclusion or "")
    lim = [s for s in reader.future_sentences(text) if "limitation" in s.lower()]
    fut = [s for s in reader.future_sentences(text) if s not in lim]
    return {"methods": _hits(text, METHODS, ui), "data": _hits(text, DATA, ui),
            "result": reader.result_sentences(text, 2), "limits": lim[:3], "future": fut[:3]}


def review(papers, ui="sr"):
    """papers: dict-ovi sa title, venue, link, abstract, finding. Vraća strukturu za prikaz."""
    meth, data, venues = Counter(), Counter(), Counter()
    open_q = []
    for p in papers:
        txt = (p.get("abstract") or "") + " " + (p.get("conclusion") or "")
        meth.update(set(_hits(txt, METHODS, ui)))
        data.update(set(_hits(txt, DATA, ui)))
        if p.get("venue"):
            venues[p["venue"]] += 1
        open_q += [(s, p) for s in reader.future_sentences(txt)[:2]]
    strong = [p for p in papers if re.search(r"outperform|significant|improv|reduc|higher|lower|%|nadmaš|značaj|poboljš",
                                             (p.get("finding") or "").lower())]
    return {"n": len(papers), "methods": meth.most_common(8), "data": data.most_common(6),
            "venues": venues.most_common(5), "highlights": (strong or papers)[:8], "open": open_q[:8]}


# Mapa praznina: koliko radova postoji za kombinaciju metod x problem (OpenAlex, poslednje 2 godine)
GAP_METHODS = [
    ("LSTM / duboko učenje", "LSTM / deep learning", '"LSTM" OR "deep learning"'),
    ("Transformer", "Transformer", '"transformer"'),
    ("Učenje podsticanjem", "Reinforcement learning", '"reinforcement learning"'),
    ("Fazi logika", "Fuzzy logic", '"fuzzy"'),
    ("ANFIS / neuro-fazi", "ANFIS / neuro-fuzzy", '"ANFIS" OR "neuro-fuzzy"'),
    ("Veliki jezički modeli", "Large language models", '"large language model" OR "LLM"'),
    ("Objašnjiva AI", "Explainable AI", '"explainable" OR "SHAP"'),
    ("Konformalna predikcija", "Conformal prediction", '"conformal prediction"'),
    ("Učenje usmereno na odluku", "Decision-focused learning", '"decision-focused" OR "predict-then-optimize" OR "end-to-end portfolio"'),
]
GAP_PROBLEMS = [
    ("Optimizacija portfolija", "Portfolio optimisation", '"portfolio optimization" OR "portfolio selection"'),
    ("Alokacija imovine", "Asset allocation", '"asset allocation"'),
    ("Profil rizika investitora", "Investor risk profiling", '"risk tolerance" OR "risk profiling" OR "investor profile"'),
    ("Robo-savetnici", "Robo-advisors", '"robo-advisor" OR "robo-advisory" OR "robo advisor"'),
    ("Greška procene / 1/N", "Estimation error / 1/N", '"estimation error" OR "naive diversification"'),
    ("Tržišta u razvoju", "Emerging markets", '"emerging market" OR "frontier market"'),
]


def gap_ideas(cells, ui="sr", top=6):
    """cells: {(mi, pi): count}. Praznina = kombinacija mnogo ređa nego što bi se očekivalo po veličini oba polja."""
    rows = {mi: sum(c for (m, _), c in cells.items() if m == mi) for mi in range(len(GAP_METHODS))}
    cols = {pi: sum(c for (_, p), c in cells.items() if p == pi) for pi in range(len(GAP_PROBLEMS))}
    total = sum(cells.values()) or 1
    ideas = []
    for (mi, pi), c in cells.items():
        exp = rows[mi] * cols[pi] / total
        if exp < 3 or rows[mi] < 15 or cols[pi] < 15:
            continue
        ideas.append(((c + 1) / (exp + 1), mi, pi, c, exp))
    ideas.sort()
    out = []
    for ratio, mi, pi, c, exp in ideas[:top]:
        m = GAP_METHODS[mi][0 if ui == "sr" else 1]
        pr = GAP_PROBLEMS[pi][0 if ui == "sr" else 1]
        out.append({"method": m, "problem": pr, "count": c, "expected": exp, "ratio": ratio,
                    "query": f'{GAP_METHODS[mi][2]} {GAP_PROBLEMS[pi][2]}'})
    return out
