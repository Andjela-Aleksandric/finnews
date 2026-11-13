const SUPABASE_URL = (import.meta.env.VITE_SUPABASE_URL || "").replace(/\/$/, "");
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || "";
const ITERATIONS = 600000;

export const portfolioCloudConfigured = () => !!(SUPABASE_URL && SUPABASE_ANON_KEY);

const b64 = (bytes) => {
  let binary = "";
  for (let i = 0; i < bytes.length; i += 0x8000) binary += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(binary);
};
const unb64 = (value) => Uint8Array.from(atob(value), (c) => c.charCodeAt(0));

async function derive(password, salt) {
  const material = await crypto.subtle.importKey("raw", new TextEncoder().encode(password), "PBKDF2", false, ["deriveBits"]);
  const raw = new Uint8Array(await crypto.subtle.deriveBits({ name: "PBKDF2", salt, iterations: ITERATIONS, hash: "SHA-256" }, material, 512));
  const key = await crypto.subtle.importKey("raw", raw.slice(0, 32), { name: "AES-GCM" }, false, ["encrypt", "decrypt"]);
  const verifierBytes = new Uint8Array(await crypto.subtle.digest("SHA-256", raw.slice(32)));
  const verifier = [...verifierBytes].map((x) => x.toString(16).padStart(2, "0")).join("");
  raw.fill(0);
  return { key, verifier };
}

async function api(action, name, extra = {}) {
  if (!portfolioCloudConfigured()) throw new Error("Cloud čuvanje još nije podešeno za ovu aplikaciju.");
  if (!crypto.subtle) throw new Error("Šifrovano čuvanje zahteva HTTPS vezu.");
  let r;
  try {
    r = await fetch(`${SUPABASE_URL}/functions/v1/portfolios`, {
      method: "POST",
      headers: { "Content-Type": "application/json", apikey: SUPABASE_ANON_KEY, Authorization: `Bearer ${SUPABASE_ANON_KEY}` },
      body: JSON.stringify({ action, name, ...extra }),
    });
  } catch {
    throw new Error("Ne mogu da povežem sa Supabase servisom. Proveri da li je Edge Function `portfolios` objavljena u projektu čiji je Project URL unet u GitHub Actions → Variables → SUPABASE_URL, i da li URL pripada tom projektu. Ako jeste, proveri da funkcija dozvoljava CORS zahtev sa ovog sajta.");
  }
  let body = {};
  try { body = await r.json(); } catch { /* non-JSON error */ }
  if (!r.ok) {
    if (r.status === 401) throw new Error("Naziv ili lozinka nisu ispravni.");
    if (r.status === 404) throw new Error("Portfolio sa ovim nazivom nije pronađen.");
    if (r.status === 429) throw new Error("Previše pokušaja. Sačekaj malo pa pokušaj ponovo.");
    throw new Error(body.error || `Cloud servis je vratio grešku (${r.status}).`);
  }
  return body;
}

function checkCredentials(name, password) {
  if (!name || !name.trim()) throw new Error("Unesi naziv portfolija.");
  if (!password || password.length < 10) throw new Error("Lozinka mora imati najmanje 10 znakova.");
}

export async function saveCloudPortfolio(name, password, state) {
  checkCredentials(name, password);
  const cleanName = name.trim();
  const record = await api("lookup", cleanName);
  const salt = record.exists ? unb64(record.salt) : crypto.getRandomValues(new Uint8Array(16));
  const { key, verifier } = await derive(password, salt);
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const plain = new TextEncoder().encode(JSON.stringify({ ...state, cloudName: cleanName }));
  const cipher = new Uint8Array(await crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, plain));
  await api("save", cleanName, { salt: b64(salt), iv: b64(iv), verifier, cipher: b64(cipher), iterations: ITERATIONS });
}

export async function loadCloudPortfolio(name, password) {
  checkCredentials(name, password);
  const cleanName = name.trim();
  const record = await api("lookup", cleanName);
  if (!record.exists) throw new Error("Portfolio sa ovim nazivom nije pronađen.");
  const salt = unb64(record.salt);
  const { key, verifier } = await derive(password, salt);
  const saved = await api("load", cleanName, { verifier });
  try {
    const plain = await crypto.subtle.decrypt({ name: "AES-GCM", iv: unb64(saved.iv) }, key, unb64(saved.cipher));
    const state = JSON.parse(new TextDecoder().decode(plain));
    if (!state || !Array.isArray(state.txns) || !Array.isArray(state.assets)) throw new Error("Invalid data");
    return state;
  } catch {
    throw new Error("Lozinka nije ispravna ili je sačuvani portfolio oštećen.");
  }
}
