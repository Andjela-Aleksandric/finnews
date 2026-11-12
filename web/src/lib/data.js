import { useEffect, useState } from "react";

let META = null;
const cache = {};

export async function loadMeta() {
  if (META) return META;
  const r = await fetch(`data/meta.json?t=${Date.now()}`, { cache: "no-store" });
  META = await r.json();
  return META;
}
export function getMeta() {
  return META;
}
export function load(name) {
  if (!cache[name]) {
    const v = encodeURIComponent((META && META.generated) || "");
    cache[name] = fetch(`data/${name}?v=${v}`).then((r) => (r.ok ? r.json() : null)).catch(() => null);
  }
  return cache[name];
}
export function useData(names) {
  const list = Array.isArray(names) ? names : [names];
  const key = list.join("|");
  const [state, setState] = useState({ loading: true, data: list.map(() => null) });
  useEffect(() => {
    let live = true;
    setState((s) => ({ ...s, loading: true }));
    Promise.all(list.map((n) => (n ? load(n) : Promise.resolve(null)))).then((data) => live && setState({ loading: false, data }));
    return () => { live = false; };
  }, [key]); // eslint-disable-line
  return state;
}

// vesti za period: poslednjih 8 dana su u recent.json, starije u mesečnim fajlovima
export function newsFiles(days) {
  const files = ["news/recent.json"];
  if (days > 7 && META) {
    const cut = new Date(Date.now() - days * 864e5).toISOString().slice(0, 7);
    for (const m of META.months || []) if (m >= cut) files.push(`news/${m}.json`);
  }
  return files;
}
export function useNews(days) {
  const files = newsFiles(days);
  const { loading, data } = useData(files);
  const since = new Date(Date.now() - days * 864e5).toISOString();
  const seen = new Set();
  const items = [];
  for (const arr of data) for (const it of arr || []) if (it.p >= since && !seen.has(it.id)) { seen.add(it.id); items.push(it); }
  return { loading, items };
}

// cene: datumi su sažeti ("MM-DD" kad se godina ne menja)
const pcache = {};
export function series(prices, t) {
  if (!prices || !prices[t]) return [];
  if (pcache[t] && pcache[t].src === prices[t]) return pcache[t].out;
  const p = prices[t];
  let year = p.d0.slice(0, 4);
  const out = p.d.map((d, i) => {
    if (d.length > 5) year = d.slice(0, 4);
    return { time: d.length > 5 ? d : `${year}-${d}`, value: p.c[i] };
  });
  pcache[t] = { src: prices[t], out };
  return out;
}

// sačuvane vesti i podešavanja u pregledaču
export const store = {
  get(k, d) { try { const v = localStorage.getItem("fn_" + k); return v === null ? d : JSON.parse(v); } catch { return d; } },
  set(k, v) { try { localStorage.setItem("fn_" + k, JSON.stringify(v)); } catch { /* privatni režim */ } },
};

// tokenizacija i spajanje vesti o istoj temi (isto kao na serveru)
const STOP = new Set("the a an of to in on for and or with as at by from is are was were be has have will its after over into amid says said new more than this that what how why who about up down".split(" "));
export const tokens = (t) => new Set((t.toLowerCase().match(/[a-zčćšžđ0-9&]+/g) || []).filter((w) => w.length > 2 && !STOP.has(w)));
export function dedupe(items, limit) {
  const kept = [], extra = {}, toks = [];
  for (const it of items) {
    const tk = tokens(it.t);
    let dup = -1;
    for (let i = 0; i < toks.length; i++) {
      let inter = 0;
      for (const w of tk) if (toks[i].has(w)) inter++;
      const uni = tk.size + toks[i].size - inter;
      if (tk.size && inter >= 3 && inter / uni >= 0.3) { dup = i; break; }
    }
    if (dup < 0) { kept.push(it); toks.push(tk); } else extra[kept[dup].id] = (extra[kept[dup].id] || 0) + 1;
    if (kept.length >= limit) break;
  }
  return { kept, extra };
}
export function relevance(it, days) {
  const half = days <= 1 ? 18 : days * 8;
  const age = Math.max(0, (Date.now() - new Date(it.p).getTime()) / 36e5);
  return (it.k || 0) * (0.35 + 0.65 * Math.pow(0.5, age / half));
}
