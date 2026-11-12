// Obračun portfolija u pregledaču (ista pravila kao u Python verziji).
import { series } from "./data";

const last = (s) => (s.length ? s[s.length - 1].value : null);
const prevv = (s) => (s.length > 1 ? s[s.length - 2].value : null);

export function positions(state) {
  const pos = {};
  const tx = [...(state.txns || [])].filter((t) => t.status === "filled").sort((a, b) => (a.d || "").localeCompare(b.d || ""));
  for (const t of tx) {
    const p = (pos[t.ticker] ||= { ticker: t.ticker, name: t.name, isin: t.isin, qty: 0, cost: 0, realized: 0 });
    const fee = +t.fee || 0;
    if (t.side === "buy") { p.qty += +t.qty; p.cost += +t.qty * (+t.price || 0) + fee; }
    else {
      const avg = p.qty ? p.cost / p.qty : 0;
      const sold = Math.min(+t.qty, p.qty);
      p.realized += sold * (+t.price || 0) - fee - sold * avg;
      p.cost -= sold * avg; p.qty -= sold;
    }
  }
  return Object.values(pos).filter((p) => p.qty > 1e-9);
}

export function valuation(state, prices, stockMap) {
  const fx = series(prices, "EURUSD=X");
  const usd = last(fx);
  const out = positions(state).map((p) => {
    const s = series(prices, p.ticker);
    const cur = (stockMap[p.ticker] && stockMap[p.ticker].currency) || (p.ticker.includes(".") ? "EUR" : "USD");
    const rate = cur === "USD" && usd ? 1 / usd : 1;
    const price = last(s), pv = prevv(s);
    const value = price ? p.qty * price * rate : null;
    return { ...p, price, currency: cur, value, avg: p.qty ? p.cost / p.qty : null, pl: value !== null ? value - p.cost : null,
      plPct: value && p.cost ? value / p.cost - 1 : null, day: price && pv ? price / pv - 1 : null,
      dayEur: price && pv ? p.qty * (price - pv) * rate : null, series: s, rate };
  });
  return out.sort((a, b) => (b.value || 0) - (a.value || 0));
}

export function goldEur(prices, i = null) {
  const g = series(prices, "GC=F"), fx = series(prices, "EURUSD=X");
  if (!g.length || !fx.length) return null;
  const fmap = Object.fromEntries(fx.map((x) => [x.time, x.value]));
  const pts = g.filter((x) => fmap[x.time]).map((x) => ({ time: x.time, value: x.value / fmap[x.time] }));
  return i === null ? pts : pts;
}
export function eurRsd(prices) {
  const v = last(series(prices, "EURRSD=X"));
  return v && v > 100 && v < 140 ? v : 117.2;
}

export function assetValues(state, prices) {
  const rsd = eurRsd(prices);
  const gold = goldEur(prices) || [];
  const gNow = gold.length ? gold[gold.length - 1].value : null;
  const gPrev = gold.length > 1 ? gold[gold.length - 2].value : null;
  return (state.assets || []).map((a) => {
    const fx = a.currency === "RSD" ? 1 / rsd : a.currency === "USD" ? 1 / (last(series(prices, "EURUSD=X")) || 1.08) : 1;
    const base = +a.amount * fx;
    let value = base, extra = null, day = 0;
    if (a.kind === "gold" && a.gold_base && gNow) { value = base * gNow / a.gold_base; extra = gNow / a.gold_base - 1; day = gPrev ? gNow / gPrev - 1 : 0; }
    if ((a.kind === "bond" || a.kind === "savings") && a.rate) {
      const days = a.start ? Math.max(0, (Date.now() - new Date(a.start).getTime()) / 864e5) : 0;
      const interest = +a.amount * a.rate * days / 365;
      value = (+a.amount + interest) * fx; extra = interest;
    }
    return { ...a, base, value, extra, day, dayEur: a.kind === "gold" ? value * day / (1 + day) : 0 };
  });
}

// kretanje ukupne vrednosti sadašnjeg portfolija kroz vreme
export function history(state, prices, stockMap, days = 365) {
  const vals = valuation(state, prices, stockMap);
  const av = assetValues(state, prices);
  const gold = Object.fromEntries((goldEur(prices) || []).map((x) => [x.time, x.value]));
  const goldPts = Object.keys(gold).sort();
  const gNow = goldPts.length ? gold[goldPts[goldPts.length - 1]] : null;
  const fx = Object.fromEntries(series(prices, "EURUSD=X").map((x) => [x.time, x.value]));
  const cut = new Date(Date.now() - days * 864e5).toISOString().slice(0, 10);
  const dates = new Set();
  for (const v of vals) for (const p of v.series) if (p.time >= cut) dates.add(p.time);
  const sorted = [...dates].sort();
  const lastPx = {};
  const out = [];
  for (const d of sorted) {
    let sec = 0, ok = true;
    for (const v of vals) {
      const m = v.series.find((p) => p.time === d);
      if (m) lastPx[v.ticker] = m.value;
      if (lastPx[v.ticker] === undefined) { ok = false; continue; }
      const rate = v.currency === "USD" ? 1 / (fx[d] || 1.08) : 1;
      sec += v.qty * lastPx[v.ticker] * rate;
    }
    if (!ok) continue;
    let tot = sec;
    const back = (Date.now() - new Date(d).getTime()) / 864e5;
    for (const a of av) {
      if (a.kind === "gold" && gNow && gold[d]) tot += a.value * gold[d] / gNow;
      else if ((a.kind === "bond" || a.kind === "savings") && a.rate) tot += a.value / (1 + a.rate * back / 365);
      else tot += a.value;
    }
    out.push({ time: d, value: tot, sec });
  }
  return out;
}

export const KIND = {
  gold: ["Zlato (indeks)", "Gold (index)"], bond: ["Obveznice", "Bonds"], savings: ["Štednja", "Savings"], cash: ["Gotovina", "Cash"], other: ["Ostalo", "Other"],
};
