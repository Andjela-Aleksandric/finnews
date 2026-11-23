import json, sys, time, requests
URL = "http://localhost:11434"
ART = """The Federal Reserve held its benchmark interest rate steady at 3.75% to 4.00% on Wednesday, but Chair Jerome Powell signaled that a December cut is far from certain as inflation remains above the 2% target. Core PCE inflation rose 2.9% in September from a year earlier. Two officials dissented in favor of a quarter-point cut. Treasury yields rose after the decision, with the 2-year yield climbing 8 basis points to 3.62%, while the S&P 500 fell 0.8%. Powell said the labor market has cooled, with unemployment at 4.3%, but that tariffs continue to push up goods prices. Futures markets cut the probability of a December move to 45% from 70% before the meeting. Bank stocks gained while rate-sensitive technology shares lagged. Analysts at Goldman Sachs now expect only one cut in the first quarter of 2027.""" * 2
NEWS = [("Nvidia beats estimates, guides revenue to $62 billion", "Nvidia reported quarterly revenue of $57 billion, up 62% year on year, driven by data center sales of $51 billion. It guided next-quarter revenue to $62 billion, above estimates of $61.4 billion."),
        ("ECB keeps rates at 2%, Lagarde says policy is in a good place", "The European Central Bank kept its deposit rate at 2% for a fourth meeting. Inflation in the euro area was 2.1% in October."),
        ("Oil falls 3% as OPEC+ signals more supply", "Brent crude fell 3% to $62 a barrel after OPEC+ said it would raise output by 137,000 barrels per day in December."),
        ("Fed holds rates, Powell says December cut not a foregone conclusion", ART[:400]),
        ("Bitcoin drops below $90,000 as risk appetite fades", "Bitcoin fell 6% to $88,500, its lowest level since April, as investors pulled $3 billion from crypto ETFs in November.")]
def gen(model, prompt, n, js=False):
    body = {"model": model, "prompt": prompt, "stream": False, "think": False, "options": {"temperature": 0.2, "num_predict": n, "num_ctx": 4096}}
    if js: body["format"] = "json"
    t = time.time(); r = requests.post(f"{URL}/api/generate", json=body, timeout=900); d = r.json()
    if "error" in d: body.pop("think"); t = time.time(); d = requests.post(f"{URL}/api/generate", json=body, timeout=900).json()
    return time.time() - t, (d.get("response") or "").strip(), d.get("eval_count"), d.get("prompt_eval_count")
model = sys.argv[1]
s, out, ev, pe = gen(model, "Summarize this financial news article for an investor in 2 to 3 sentences. Start with the main fact and keep every number exactly.\n\nARTICLE: " + ART, 180)
print(f"== {model} BRIEF {s:.1f}s out_tokens={ev} prompt_tokens={pe}\n{out}\n")
rows = "\n".join(f"[{i}] {a} - {b}" for i, (a, b) in enumerate(NEWS, 1))
s, out, ev, pe = gen(model, "Below are financial news items. Write 3 to 5 bullet points explaining what happened and why it matters for investors. Each bullet ends with item numbers like [1]. Answer as JSON: {\"points\": [\"...\"]}\n\n" + rows, 460, True)
print(f"== {model} DIGEST {s:.1f}s out_tokens={ev}\n{out}\n")
s, out, ev, pe = gen(model, "You are a senior portfolio strategist. From these news items, give an investor briefing as JSON with keys: regime (one sentence on the market environment), risks (2-3 items), opportunities (2-3 items), watch (2-3 upcoming things to monitor). Each item is one sentence ending with item numbers like [2]. Use only facts in the items.\n\n" + rows, 600, True)
print(f"== {model} STRATEGIST {s:.1f}s out_tokens={ev}\n{out}\n")
