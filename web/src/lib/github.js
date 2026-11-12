// Pristup privatnom repozitorijumu (portfolio i celi tekstovi) - samo za vlasnika, ključ se čuva u ovom pregledaču.
import { store } from "./data";

export const owner = {
  get() { return store.get("owner", null); },
  set(v) { store.set("owner", v); },
  clear() { try { localStorage.removeItem("fn_owner"); } catch { /* */ } },
};
const API = "https://api.github.com";
const hdr = (tok, raw) => ({ Authorization: `Bearer ${tok}`, Accept: raw ? "application/vnd.github.raw+json" : "application/vnd.github+json" });

function b64encode(str) {
  const bytes = new TextEncoder().encode(str);
  let bin = "";
  for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(bin);
}
function b64decode(b64) {
  const bin = atob(b64.replace(/\n/g, ""));
  return new TextDecoder().decode(Uint8Array.from(bin, (c) => c.charCodeAt(0)));
}

export async function testOwner(o) {
  const r = await fetch(`${API}/repos/${o.repo}`, { headers: hdr(o.token) });
  if (!r.ok) throw new Error(r.status === 404 ? "Repozitorijum nije pronađen ili ključ nema pristup" : `GitHub ${r.status}`);
  return true;
}
export async function loadPortfolio() {
  const o = owner.get();
  if (!o) return null;
  const r = await fetch(`${API}/repos/${o.repo}/contents/data/portfolio.json?t=${Date.now()}`, { headers: hdr(o.token), cache: "no-store" });
  if (r.status === 404) return { state: { version: 1, changed: "", txns: [], assets: [], watchlist: [] }, sha: null };
  if (!r.ok) throw new Error(`GitHub ${r.status}`);
  const j = await r.json();
  return { state: JSON.parse(b64decode(j.content)), sha: j.sha };
}
export async function savePortfolio(state, sha) {
  const o = owner.get();
  const body = { message: "FinNews: portfolio (web)", content: b64encode(JSON.stringify({ ...state, changed: new Date().toISOString().slice(0, 19) + "+00:00" }, null, 1)) };
  if (sha) body.sha = sha;
  const r = await fetch(`${API}/repos/${o.repo}/contents/data/portfolio.json`, { method: "PUT", headers: { ...hdr(o.token), "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!r.ok) throw new Error(r.status === 409 ? "Portfolio je u međuvremenu izmenjen na drugom uređaju - osveži stranicu." : `GitHub ${r.status}`);
  const j = await r.json();
  return j.content.sha;
}
const tcache = {};
export function loadTexts(day) {
  const o = owner.get();
  if (!o) return Promise.resolve(null);
  if (!tcache[day]) {
    tcache[day] = fetch(`${API}/repos/${o.repo}/contents/texts/${day}.json?ref=texts`, { headers: hdr(o.token, true) })
      .then((r) => (r.ok ? r.json() : {})).catch(() => ({}));
  }
  return tcache[day];
}
