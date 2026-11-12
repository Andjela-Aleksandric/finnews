#!/bin/bash
# FinNews na internetu - link koji radi na telefonu i kada je Mac ugašen.
# Besplatno: kod ide u tvoj PRIVATNI GitHub repozitorijum, aplikacija radi na Streamlit Community Cloud-u,
# a portfolio se sinhronizuje između Mac-a i telefona preko drugog privatnog repozitorijuma (finnews-data).
# Pokreni:  bash ~/finnews/deploy_cloud.sh   (isto i za kasnija ažuriranja koda)
set -e
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
VPY="$APP_DIR/.venv/bin/python"
[ -x "$VPY" ] || { echo "Prvo pokreni instalaciju: bash $APP_DIR/install.sh"; exit 1; }

if ! command -v gh >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then echo "→ Instaliram GitHub alat (gh)..."; brew install gh
  else echo "Treba ti GitHub alat: instaliraj Homebrew (https://brew.sh) pa pokreni ponovo."; exit 1; fi
fi
if ! gh auth status >/dev/null 2>&1; then
  echo "→ Prijava na GitHub (otvoriće se pregledač; ako nemaš nalog, napravi ga besplatno na github.com)..."
  gh auth login --hostname github.com --git-protocol https --web --scopes repo
fi
GHUSER="$(gh api user -q .login)"
CODE="$GHUSER/finnews"
DATA="$GHUSER/finnews-data"

PINFILE="$HOME/Library/Application Support/FinNews/.cloud_pin"
if [ -f "$PINFILE" ]; then PIN="$(cat "$PINFILE")"; else
  read -r -s -p "  Izaberi PIN za Portfolio i Podešavanja na internetu (najmanje 4 znaka): " PIN; echo
  [ ${#PIN} -ge 4 ] || { echo "PIN je prekratak."; exit 1; }
  printf "%s" "$PIN" > "$PINFILE"; chmod 600 "$PINFILE"
fi

echo "→ Šaljem kod u privatni repozitorijum $CODE ..."
TMP="$(mktemp -d)"
rsync -a --exclude .venv --exclude __pycache__ --exclude "widgets/swiftbar" --exclude ".git" --exclude personal_seed.json \
  --exclude "web/node_modules" --exclude "web/dist" --exclude "web/public/data" --exclude "web/private_texts" --exclude ".data" "$APP_DIR/" "$TMP/finnews/"
cd "$TMP/finnews"
git init -q -b main && git add . && git -c user.name="FinNews" -c user.email="finnews@local" commit -qm "FinNews $(date +%Y-%m-%d)"
if gh repo view "$CODE" >/dev/null 2>&1; then
  git remote add origin "https://github.com/$CODE.git" && gh auth setup-git >/dev/null 2>&1 && git push -q -f origin main
else
  gh repo create "$CODE" --private --source . --push >/dev/null
fi
gh repo view "$DATA" >/dev/null 2>&1 || gh repo create "$DATA" --private --add-readme -d "FinNews portfolio (privatno)" >/dev/null
cd "$APP_DIR"

TOKEN="$(gh auth token)"
echo "→ Povezujem Mac sa sinhronizacijom portfolija..."
FINNEWS_PIN="$PIN" GH_TOKEN_X="$TOKEN" GH_REPO_X="$DATA" "$VPY" - <<'PY'
import os, hashlib, ai, db, cloud_sync
cfg = ai.load_config()
cfg["github_token"], cfg["github_repo"] = os.environ["GH_TOKEN_X"], os.environ["GH_REPO_X"]
cfg["pin_hash"] = hashlib.sha256(("finnews:" + os.environ["FINNEWS_PIN"].strip()).encode()).hexdigest()
ai.save_config(cfg)
print("  portfolio:", cloud_sync.pull(db.connect()))
PY

DONE="$HOME/Library/Application Support/FinNews/.cloud_deployed"
if [ -f "$DONE" ]; then
  echo ""
  echo "✓ Novi kod je poslat. Tvoja aplikacija na internetu se sama osvežava za 2-3 minuta - ništa ne treba da radiš na sajtu."
  exit 0
fi
touch "$DONE"
SECRETS="FINNEWS_PUBLIC = \"1\"
FINNEWS_PIN = \"$PIN\"
GITHUB_TOKEN = \"$TOKEN\"
FINNEWS_REPO = \"$DATA\""
command -v pbcopy >/dev/null && printf "%s" "$SECRETS" | pbcopy
cat <<EOT

════════════════════════════════════════════════════════════════════
  Kod je na GitHub-u. Još jedan korak (samo prvi put, ~2 minuta):

  1. Otvara se share.streamlit.io - prijavi se istim GitHub nalogom.
  2. Klikni "Create app" → "Deploy a public app from GitHub":
       Repository:  $CODE
       Branch:      main
       Main file:   app.py
       App URL:     npr. finnews-$GHUSER  (to je tvoj stalni link)
  3. "Advanced settings" → Secrets → nalepi (već je kopirano, Cmd+V):

$SECRETS

  4. Deploy. Za 2-3 minuta dobijaš link koji radi bilo gde.
     Na telefonu: Share → Add to Home Screen.

  Kasnije izmene koda: samo ponovo pokreni ovu komandu.
  Portfolio se sam sinhronizuje između Mac-a i telefona.
════════════════════════════════════════════════════════════════════
EOT
open "https://share.streamlit.io/deploy" 2>/dev/null || true
