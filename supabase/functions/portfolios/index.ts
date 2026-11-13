import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Content-Type": "application/json",
};
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: cors });
const encoder = new TextEncoder();
const hex = (bytes: Uint8Array) => [...bytes].map((b) => b.toString(16).padStart(2, "0")).join("");
async function digest(value: string) {
  return hex(new Uint8Array(await crypto.subtle.digest("SHA-256", encoder.encode(value))));
}
function sameSecret(a: string, b: string) {
  if (!a || !b || a.length !== b.length) return false;
  let mismatch = 0;
  for (let i = 0; i < a.length; i++) mismatch |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return mismatch === 0;
}
function validBase64(value: unknown, maxLength: number) {
  return typeof value === "string" && value.length > 0 && value.length <= maxLength && /^[A-Za-z0-9+/]+={0,2}$/.test(value);
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return json({ error: "Method not allowed." }, 405);

  const url = Deno.env.get("SUPABASE_URL");
  const serviceRole = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !serviceRole) return json({ error: "Cloud service is not configured." }, 503);

  let body: Record<string, unknown>;
  try {
    const raw = await req.text();
    if (raw.length > 3_000_000) return json({ error: "Portfolio is too large." }, 413);
    body = JSON.parse(raw);
  } catch {
    return json({ error: "Invalid request." }, 400);
  }

  const action = String(body.action || "");
  const name = typeof body.name === "string" ? body.name.trim().normalize("NFKC") : "";
  if (!name || name.length > 80) return json({ error: "Enter a portfolio name (up to 80 characters)." }, 400);
  if (!["lookup", "save", "load"].includes(action)) return json({ error: "Unsupported action." }, 400);

  const supabase = createClient(url, serviceRole, { auth: { persistSession: false } });
  const profileId = await digest(name.toLocaleLowerCase("en-US"));
  const ip = req.headers.get("cf-connecting-ip") || req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "unknown";
  const bucket = await digest(`${ip}:${profileId}`);
  const { data: allowed, error: rateError } = await supabase.rpc("consume_portfolio_attempt", {
    p_bucket_key: bucket, p_now: new Date().toISOString(), p_limit: 30, p_window_seconds: 900,
  });
  if (rateError) {
    console.error("portfolio rate limit:", rateError.message);
    return json({ error: "Cloud service is temporarily unavailable." }, 503);
  }
  if (!allowed) return json({ error: "Too many attempts. Wait and try again." }, 429);

  const { data: row, error: readError } = await supabase.from("saved_portfolios")
    .select("portfolio_id, display_name, salt, verifier, iv, cipher, iterations, updated_at")
    .eq("portfolio_id", profileId).maybeSingle();
  if (readError) {
    console.error("portfolio read:", readError.message);
    return json({ error: "Cloud service is temporarily unavailable." }, 503);
  }

  if (action === "lookup") return json(row ? { exists: true, salt: row.salt } : { exists: false });

  const verifier = typeof body.verifier === "string" ? body.verifier : "";
  if (!/^[0-9a-f]{64}$/.test(verifier)) return json({ error: "Invalid password proof." }, 400);

  if (action === "load") {
    if (!row) return json({ error: "Portfolio not found." }, 404);
    if (!sameSecret(row.verifier, verifier)) return json({ error: "Name or password is incorrect." }, 401);
    return json({ salt: row.salt, iv: row.iv, cipher: row.cipher, updatedAt: row.updated_at });
  }

  const salt = body.salt;
  const iv = body.iv;
  const cipher = body.cipher;
  const iterations = Number(body.iterations);
  if (!validBase64(salt, 64) || !validBase64(iv, 64) || !validBase64(cipher, 2_800_000) || iterations !== 600000) {
    return json({ error: "Invalid encrypted portfolio data." }, 400);
  }
  try {
    if (atob(String(salt)).length !== 16 || atob(String(iv)).length !== 12) return json({ error: "Invalid encryption parameters." }, 400);
  } catch {
    return json({ error: "Invalid encryption parameters." }, 400);
  }

  const values = { display_name: name, salt, verifier, iv, cipher, iterations, updated_at: new Date().toISOString() };
  if (row) {
    if (!sameSecret(row.verifier, verifier)) return json({ error: "Name or password is incorrect." }, 401);
    if (row.salt !== salt) return json({ error: "Encryption key mismatch. Reload the saved portfolio first." }, 409);
    const { error } = await supabase.from("saved_portfolios").update(values).eq("portfolio_id", profileId);
    if (error) {
      console.error("portfolio update:", error.message);
      return json({ error: "Could not save portfolio." }, 503);
    }
  } else {
    const { error } = await supabase.from("saved_portfolios").insert({ portfolio_id: profileId, ...values });
    if (error) {
      console.error("portfolio insert:", error.message);
      return json({ error: error.code === "23505" ? "Portfolio was created on another device. Try opening it." : "Could not save portfolio." }, error.code === "23505" ? 409 : 503);
    }
  }
  return json({ saved: true, updatedAt: values.updated_at });
});
