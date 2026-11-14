"""Besplatan lokalni AI (Ollama + mali otvoreni model) za sažetke vesti, nalaze studija i preglede perioda.

Radi u GitHub Action-u (CPU, bez ključa i bez troškova) i na Mac-u ako je Ollama pokrenuta.
Model piše na engleskom (mali modeli tu najbolje rade), a prevod na srpski ide postojećim putem
(Google + pravila za prirodan srpski i imena u izvornom obliku). Sve se kešira u bazi, pa se
model poziva samo za nove vesti i kad se promeni sastav najvažnijih vesti u periodu."""
import json
import os
import re
import time

import requests

URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL = os.environ.get("FINNEWS_OLLAMA_MODEL", "qwen2.5:3b")
_DEADLINE = [0.0]


def available():
    try:
        r = requests.get(f"{URL}/api/tags", timeout=2)
        names = [m.get("name", "") for m in r.json().get("models", [])]
        return any(n == MODEL or n == MODEL + ":latest" or n.startswith(MODEL + "-") for n in names)
    except Exception:  # noqa: BLE001
        return False


def start_budget(seconds):
    _DEADLINE[0] = time.time() + seconds


def time_left():
    return _DEADLINE[0] - time.time()


def gen(prompt, max_tokens=300, json_mode=False):
    body = {"model": MODEL, "prompt": prompt, "stream": False,
            "options": {"temperature": 0.2, "num_predict": max_tokens, "num_ctx": 4096}}
    if json_mode:
        body["format"] = "json"
    r = requests.post(f"{URL}/api/generate", json=body, timeout=240)
    r.raise_for_status()
    return (r.json().get("response") or "").strip()


_RULES = ("Rules: use ONLY facts stated in the text. Keep every number, percentage, date and amount exactly as written. "
          "Keep names of people and companies exactly as written. No opinions, no advice, no information that is not in the text. "
          "Plain, clear sentences. Never use semicolons.")


def news_brief(title, text):
    """2-3 rečenice: šta se desilo (sa brojkama), zašto je važno ako tekst to kaže, šta sledi ako je navedeno."""
    body = re.sub(r"\s+", " ", text or "")[:6000]
    out = gen(f"Summarize this financial news article for an investor in 2 to 3 sentences. Start directly with the main fact "
              f"(who did what, with the key number). Then add the most important detail or consequence stated in the text. {_RULES}\n"
              f"Return only the summary.\n\nTITLE: {title}\n\nARTICLE: {body}", max_tokens=180)
    out = re.sub(r"^(summary|here is.*?):\s*", "", out, flags=re.I).strip().replace(";", ".")
    return out if 60 < len(out) < 900 else ""


def paper_finding(title, abstract, conclusion=""):
    """(rezultat, doprinos) - rezultat odmah, sa brojkama, pa ključni doprinos studije."""
    body = re.sub(r"\s+", " ", (abstract or "") + " " + (conclusion or ""))[:5000]
    if len(body) < 200:
        return "", ""
    raw = gen("From this research abstract, extract (1) the main RESULT in 1-2 sentences: what THIS study found or achieved "
              "(a concrete outcome, ideally with numbers), not background or motivation. Start directly with the result "
              "(no 'this paper' or 'the authors'). (2) The KEY CONTRIBUTION in one sentence "
              f"(what is new: method, data or insight). {_RULES}\n"
              'Answer as JSON: {"result": "...", "contribution": "..."}\n\n'
              f"TITLE: {title}\n\nABSTRACT: {body}", max_tokens=220, json_mode=True)
    try:
        d = json.loads(raw)
        res, con = str(d.get("result") or "").strip(), str(d.get("contribution") or "").strip()
    except ValueError:
        return "", ""
    res, con = res.replace(";", "."), con.replace(";", ".")
    return (res if 30 < len(res) < 700 else ""), (con if 20 < len(con) < 400 else "")


def digest(label, items):
    """Pregled perioda: 3-5 tačaka, svaka sa brojevima vesti na koje se oslanja ([1], [3])."""
    rows = []
    for i, it in enumerate(items, 1):
        rows.append(f"[{i}] {it['title']} - {re.sub(r'\\s+', ' ', it.get('text') or '')[:420]}")
    raw = gen(f"Below are the most important financial news items for {label}. Write 3 to 5 short bullet points that together "
              "explain what happened and why it matters. Merge items about the same event. Each bullet is one or two sentences "
              f"and ends with the numbers of the items it is based on, like [1] or [2][4]. {_RULES}\n"
              'Answer as JSON: {"points": ["...", "..."]}\n\n' + "\n".join(rows), max_tokens=420, json_mode=True)
    try:
        pts = [str(x).strip().replace(";", ".") for x in json.loads(raw).get("points", []) if str(x).strip()]
    except ValueError:
        return []
    return [p for p in pts if 25 < len(p) < 600][:5]


def research_digest(label, papers):
    rows = [f"[{i}] {p['title']} - {(p.get('text') or '')[:380]}" for i, p in enumerate(papers, 1)]
    raw = gen(f"Below are key findings of recent research papers ({label}). Write 3 to 5 bullet points about what this research "
              "shows overall: common results, which methods work best and open questions. Each bullet ends with the numbers of "
              f"the papers it is based on, like [1][3]. {_RULES}\n"
              'Answer as JSON: {"points": ["...", "..."]}\n\n' + "\n".join(rows), max_tokens=420, json_mode=True)
    try:
        pts = [str(x).strip().replace(";", ".") for x in json.loads(raw).get("points", []) if str(x).strip()]
    except ValueError:
        return []
    return [p for p in pts if 25 < len(p) < 600][:5]
