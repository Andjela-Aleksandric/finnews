#!/bin/bash
# FinNews veb aplikacija na GitHub Pages - besplatno, radi i kad je Mac ugašen.
#   bash ~/finnews/deploy_web.sh      (isto i za kasnija ažuriranja)
# Šta radi:
#   1. šalje kod u repozitorijum <korisnik>/finnews (bez ličnih podataka)
#   2. podešava ključ za privatni repozitorijum <korisnik>/finnews-data (portfolio i celi tekstovi)
#   3. uključuje GitHub Pages i automatsko osvežavanje na 30 minuta
set -e
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
command -v gh >/dev/null 2>&1 || { command -v brew >/dev/null 2>&1 && brew install gh || { echo "Instaliraj Homebrew (https://brew.sh) pa pokreni ponovo."; exit 1; }; }
gh auth status >/dev/null 2>&1 || gh auth login --hostname github.com --git-protocol https --web --scopes repo,workflow
gh auth status 2>&1 | grep -q "workflow" || gh auth refresh -h github.com -s workflow
GHUSER="$(gh api user -q .login)"
CODE="$GHUSER/finnews"; DATA="$GHUSER/finnews-data"
SITE="https://$(echo "$GHUSER" | tr '[:upper:]' '[:lower:]').github.io/finnews/"

gh repo view "$DATA" >/dev/null 2>&1 || gh repo create "$DATA" --private --add-readme -d "FinNews - portfolio i celi tekstovi (privatno)" >/dev/null
# portfolio sa Mac-a ide u privatni repozitorijum (ako već nije)
if [ -x "$APP_DIR/.venv/bin/python" ]; then
  GH_TOKEN_X="$(gh auth token)" GH_REPO_X="$DATA" "$APP_DIR/.venv/bin/python" - <<'PY' || true
import os, ai, db, cloud_sync
cfg = ai.load_config(); cfg["github_token"], cfg["github_repo"] = os.environ["GH_TOKEN_X"], os.environ["GH_REPO_X"]; ai.save_config(cfg)
print("  portfolio:", cloud_sync.pull(db.connect()))
PY
fi

VIS="$(gh repo view "$CODE" --json visibility -q .visibility 2>/dev/null || echo NONE)"
if [ "$VIS" = "PRIVATE" ]; then
  echo ""
  echo "  GitHub Pages je besplatan samo za JAVNE repozitorijume. Kod ($CODE) postaje javan;"
  echo "  lični podaci (portfolio, celi tekstovi) ostaju u PRIVATNOM $DATA, a stara istorija koda se briše."
  read -r -p "  Nastavi? (d/n) " ok
  [ "$ok" = "d" ] || [ "$ok" = "D" ] || exit 1
fi

echo "→ Šaljem kod..."
TMP="$(mktemp -d)"
rsync -a --exclude .venv --exclude __pycache__ --exclude "widgets/swiftbar" --exclude ".git" --exclude personal_seed.json \
  --exclude "web/node_modules" --exclude "web/dist" --exclude "web/public/data" --exclude "web/private_texts" --exclude ".data" "$APP_DIR/" "$TMP/finnews/"
cd "$TMP/finnews"
git init -q -b main && git add . && git -c user.name="FinNews" -c user.email="finnews@users.noreply.github.com" commit -qm "FinNews $(date +%Y-%m-%d)"
if [ "$VIS" = "NONE" ]; then
  gh repo create "$CODE" --public --source . --push >/dev/null
else
  gh auth setup-git >/dev/null 2>&1
  git remote add origin "https://github.com/$CODE.git" && git push -q -f origin main
  [ "$VIS" = "PRIVATE" ] && gh repo edit "$CODE" --visibility public --accept-visibility-change-consequences >/dev/null
fi
cd "$APP_DIR"

echo "→ Podešavam ključeve i GitHub Pages..."
gh auth token | gh secret set DATA_TOKEN -R "$CODE" >/dev/null
gh variable set DATA_REPO -R "$CODE" -b "$DATA" >/dev/null
gh api -X POST "repos/$CODE/pages" -f build_type=workflow >/dev/null 2>&1 || gh api -X PUT "repos/$CODE/pages" -f build_type=workflow >/dev/null 2>&1 || true
gh workflow enable site.yml -R "$CODE" >/dev/null 2>&1 || true
gh workflow run site.yml -R "$CODE" >/dev/null 2>&1 || true

cat <<EOT

════════════════════════════════════════════════════════════════════
  ✓ Gotovo. Sajt se pravi (prvi put ~15-25 minuta, jer preuzima
    vesti za 6 meseci; posle toga se osvežava sam na svakih 30 minuta).

  Tvoj link:   $SITE

  Napredak:    gh run watch -R $CODE   (ili github.com/$CODE/actions)

  Na telefonu: otvori link u Safari-ju → Share → Add to Home Screen.
  Portfolio:   na sajtu otvori Podešavanja → "Tvoj portfolio i celi
               tekstovi" i poveži ključ (uputstvo je tu, 1 minut).
════════════════════════════════════════════════════════════════════
EOT
