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


function bytesToB64(bytes) {
  let binary = "";
  for (let i = 0; i < bytes.length; i += 0x8000) binary += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(binary);
}
function b64ToBytes(value) {
  const binary = atob((value || "").replace(/\\n/g, ""));
  return Uint8Array.from(binary, (c) => c.charCodeAt(0));
}
async function portfolioFilePath(name) {
  const normalized = name.trim().normalize("NFKC").toLowerCase();
  if (!normalized) throw new Error("Unesi naziv portfolija.");
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(normalized));
  const hash = [...new Uint8Array(digest)].slice(0, 8).map((b) => b.toString(16).padStart(2, "0")).join("");
  return `data/portfolios/${hash}.json`;
}
async function portfolioKey(password, salt, iterations) {
  const material = await crypto.subtle.importKey("raw", new TextEncoder().encode(password), "PBKDF2", false, ["deriveKey"]);
  return crypto.subtle.deriveKey({ name: "PBKDF2", salt, iterations, hash: "SHA-256" }, material,
    { name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"]);
}
async function githubFile(path, token) {
  const r = await fetch(`${API}/repos/${owner.get().repo}/contents/${path}?t=${Date.now()}`, { headers: hdr(token), cache: "no-store" });
  if (r.status === 404) return null;
  if (!r.ok) throw new Error(`GitHub ${r.status}`);
  return r.json();
}
export async function saveNamedPortfolio(name, password, state) {
  const o = owner.get();
  if (!o) throw new Error("Prvo poveži privatni GitHub repozitorijum u Podešavanjima na ovom uređaju.");
  if ((password || "").length < 8) throw new Error("Lozinka mora imati najmanje 8 znakova.");
  if (!crypto.subtle) throw new Error("Šifrovanje zahteva bezbednu HTTPS vezu.");
  const path = await portfolioFilePath(name);
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const iterations = 310000;
  const key = await portfolioKey(password, salt, iterations);
  const plaintext = new TextEncoder().encode(JSON.stringify({ ...state, savedName: name.trim() }));
  const cipher = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, plaintext);
  const envelope = { version: 1, kdf: "PBKDF2-SHA-256", iterations, salt: bytesToB64(salt), iv: bytesToB64(iv), cipher: bytesToB64(new Uint8Array(cipher)) };
  const existing = await githubFile(path, o.token);
  const body = { message: `FinNews: encrypted portfolio ${name.trim()}`, content: b64encode(JSON.stringify(envelope, null, 1)) };
  if (existing && existing.sha) body.sha = existing.sha;
  const r = await fetch(`${API}/repos/${o.repo}/contents/${path}`, { method: "PUT", headers: { ...hdr(o.token), "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!r.ok) throw new Error(r.status === 409 ? "Portfolio je izmenjen na drugom uređaju; osveži stranicu i pokušaj ponovo." : `GitHub ${r.status}`);
  return true;
}
export async function loadNamedPortfolio(name, password) {
  const o = owner.get();
  if (!o) throw new Error("Prvo poveži privatni GitHub repozitorijum u Podešavanjima na ovom uređaju.");
  if ((password || "").length < 8) throw new Error("Unesi lozinku od najmanje 8 znakova.");
  if (!crypto.subtle) throw new Error("Šifrovanje zahteva bezbednu HTTPS vezu.");
  const path = await portfolioFilePath(name);
  const file = await githubFile(path, o.token);
  if (!file) return null;
  let envelope;
  try { envelope = JSON.parse(b64decode(file.content)); }
  catch { throw new Error("Sačuvani portfolio nije ispravan."); }
  try {
    if (envelope.version !== 1 || envelope.kdf !== "PBKDF2-SHA-256") throw new Error("Nepodržan format.");
    const key = await portfolioKey(password, b64ToBytes(envelope.salt), envelope.iterations);
    const plain = await crypto.subtle.decrypt({ name: "AES-GCM", iv: b64ToBytes(envelope.iv) }, key, b64ToBytes(envelope.cipher));
    const state = JSON.parse(new TextDecoder().decode(plain));
    if (!state || !Array.isArray(state.txns) || !Array.isArray(state.assets)) throw new Error("Nepotpuni podaci.");
    return state;
  } catch {
    throw new Error("Lozinka nije ispravna ili je portfolio oštećen.");
  }
}
