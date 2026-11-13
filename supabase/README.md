# FinNews portfolio cloud storage

The web app is served as a static GitHub Pages site, so it cannot store private, cross-device portfolios by itself. This small Supabase service stores only encrypted portfolio data. End users do not need GitHub accounts or tokens: they choose a portfolio name and password in the app.

## One-time app setup

1. Create a Supabase project.
2. In the Supabase SQL Editor, run `migrations/202611130001_saved_portfolios.sql`.
3. Install the Supabase CLI, then link the project and deploy the endpoint:
   ```sh
   supabase login
   supabase link --project-ref YOUR_PROJECT_REF
   supabase functions deploy portfolios
   ```
   The function uses Supabase's `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` runtime secrets. Do not place the service role key in the web app.
4. In the FinNews GitHub repository, add these Actions **variables** (not end-user settings):
   - `SUPABASE_URL`: the project URL from Supabase → Project Settings → API.
   - `SUPABASE_ANON_KEY`: the project's public anon/publishable key.
5. Run the **FinNews sajt** GitHub Action again to rebuild and publish the website.

After that setup, the portfolio page enables the name/password cloud controls. Each user can use the same site link on any device; they enter the same portfolio name and password. GitHub is not part of the user flow.

## Data and security model

- The browser derives separate encryption and verification secrets from the password with PBKDF2-SHA-256 (600,000 iterations) and encrypts the portfolio with AES-256-GCM before upload.
- The database stores a hashed portfolio identifier, salt, verifier, nonce and ciphertext. It does not receive the portfolio's readable transactions or the password.
- The table has Row Level Security enabled and direct access revoked. Only the Edge Function uses the service role key.
- The Edge Function rate-limits requests per network address and portfolio identifier.
- Portfolio names are unique across this app. Use a name unlikely to be chosen by someone else and a strong password.
- Passwords are not recoverable. If the password is lost, the encrypted portfolio cannot be opened.
- The ordinary browser-local copy remains available. Saving to cloud is explicit; loading a cloud portfolio replaces the local portfolio in that browser.
