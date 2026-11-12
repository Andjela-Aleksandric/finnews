#!/bin/bash
# FinNews - instalacija na macOS. Pokreni iz Terminala:  bash install.sh
set -e
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
NOTIFY_HOUR=8      # jutarnje obaveštenje - sat
NOTIFY_MINUTE=30   # jutarnje obaveštenje - minut
UIDN="$(id -u)"
LA="$HOME/Library/LaunchAgents"
LOGS="$HOME/Library/Logs"
mkdir -p "$LA" "$LOGS"

PY="$(command -v python3 || true)"
if [ -z "$PY" ]; then
  echo "Python 3 nije pronađen. Instaliraj ga (npr. 'brew install python' ili sa python.org) pa pokreni ponovo."
  exit 1
fi

# ugasi staru verziju ako radi
for L in server fetch notify; do launchctl bootout "gui/$UIDN/rs.andjiko.finnews.$L" 2>/dev/null || true; done
pkill -f "finnews/.venv/bin/streamlit" 2>/dev/null || true

echo "→ Instaliram pakete..."
"$PY" -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip -q
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt" -q
VPY="$APP_DIR/.venv/bin/python"

agent() {  # agent <ime> <dodatni plist xml> <argumenti...>
  local NAME="$1" EXTRA="$2"; shift 2
  local ARGS=""; for a in "$@"; do ARGS="$ARGS<string>$a</string>"; done
  cat > "$LA/rs.andjiko.finnews.$NAME.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>rs.andjiko.finnews.$NAME</string>
  <key>ProgramArguments</key><array>$ARGS</array>
  <key>WorkingDirectory</key><string>$APP_DIR</string>
  <key>StandardOutPath</key><string>$LOGS/finnews-$NAME.log</string>
  <key>StandardErrorPath</key><string>$LOGS/finnews-$NAME.log</string>
  $EXTRA
</dict></plist>
EOF
  launchctl bootstrap "gui/$UIDN" "$LA/rs.andjiko.finnews.$NAME.plist" 2>/dev/null || launchctl load "$LA/rs.andjiko.finnews.$NAME.plist" 2>/dev/null || true
}

echo "→ Pokrećem FinNews u pozadini (uvek dostupan na localhost:8765, samo na ovom Mac-u)..."
agent server "<key>RunAtLoad</key><true/><key>KeepAlive</key><true/>" \
  "$APP_DIR/.venv/bin/streamlit" run "$APP_DIR/app.py" --server.address localhost --server.port 8765
echo "→ Automatsko preuzimanje i prevod vesti na svakih 30 minuta..."
agent fetch "<key>RunAtLoad</key><true/><key>StartInterval</key><integer>1800</integer>" "$VPY" "$APP_DIR/run_fetch.py"
echo "→ Jutarnje obaveštenje svakog dana u $NOTIFY_HOUR:$(printf %02d $NOTIFY_MINUTE)..."
agent notify "<key>StartCalendarInterval</key><dict><key>Hour</key><integer>$NOTIFY_HOUR</integer><key>Minute</key><integer>$NOTIFY_MINUTE</integer></dict>" \
  "$VPY" "$APP_DIR/widgets/notify.py"

echo "→ Pravim FinNews.app (sa ikonicom)..."
APP="$HOME/Applications/FinNews.app"
rm -rf "$APP"; mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
ICONSET="$(mktemp -d)/FinNews.iconset"; mkdir -p "$ICONSET"
for s in 16 32 128 256 512; do
  sips -z $s $s "$APP_DIR/assets/icon.png" --out "$ICONSET/icon_${s}x${s}.png" >/dev/null || true
  sips -z $((s*2)) $((s*2)) "$APP_DIR/assets/icon.png" --out "$ICONSET/icon_${s}x${s}@2x.png" >/dev/null || true
done
iconutil -c icns "$ICONSET" -o "$APP/Contents/Resources/FinNews.icns" || true
cat > "$APP/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>FinNews</string>
  <key>CFBundleDisplayName</key><string>FinNews</string>
  <key>CFBundleIdentifier</key><string>rs.andjiko.finnews</string>
  <key>CFBundleExecutable</key><string>FinNews</string>
  <key>CFBundleIconFile</key><string>FinNews</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleVersion</key><string>2.0</string>
</dict></plist>
EOF
cat > "$APP/Contents/MacOS/FinNews" <<EOF
#!/bin/bash
launchctl kickstart "gui/\$(id -u)/rs.andjiko.finnews.server" >/dev/null 2>&1
for i in \$(seq 1 40); do
  /usr/bin/curl -s "http://localhost:8765/_stcore/health" >/dev/null 2>&1 && break
  sleep 0.5
done
open "http://localhost:8765"
EOF
chmod +x "$APP/Contents/MacOS/FinNews"
touch "$APP"

echo "→ Widget za menu bar..."
PLUG="$APP_DIR/widgets/swiftbar"; mkdir -p "$PLUG"
cat > "$PLUG/finnews.5m.sh" <<EOF
#!/bin/bash
# <swiftbar.hideRunInTerminal>true</swiftbar.hideRunInTerminal>
# <swiftbar.hideDisablePlugin>true</swiftbar.hideDisablePlugin>
exec "$VPY" "$APP_DIR/widgets/menubar.py"
EOF
chmod +x "$PLUG/finnews.5m.sh"
defaults write com.ameba.SwiftBar PluginDirectory "$PLUG"
if [ ! -d "/Applications/SwiftBar.app" ] && [ ! -d "$HOME/Applications/SwiftBar.app" ]; then
  if command -v brew >/dev/null 2>&1; then
    read -r -p "  Za widget u menu baru treba besplatna aplikacija SwiftBar. Da je instaliram preko Homebrew-a? (d/n) " ok
    if [ "$ok" = "d" ] || [ "$ok" = "D" ]; then
      brew install --cask swiftbar || true
      brew install terminal-notifier || true   # da klik na obaveštenje otvara FinNews
    fi
  else
    echo "  Za widget u menu baru preuzmi besplatni SwiftBar sa https://swiftbar.app i pokreni ga jednom."
    echo "  Kad pita za folder sa pluginovima, izaberi: $PLUG"
  fi
fi
open -a SwiftBar 2>/dev/null || true

if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
  read -r -p "  Želiš besplatni lokalni AI (AI brief, analize studija, predlozi tema - bez API ključa, ~3-8 GB)? (d/n) " okai
  if [ "$okai" = "d" ] || [ "$okai" = "D" ]; then bash "$APP_DIR/setup_local_ai.sh" || true; fi
fi

for i in $(seq 1 40); do curl -s "http://localhost:8765/_stcore/health" >/dev/null 2>&1 && break; sleep 0.5; done
if ! curl -s "http://localhost:8765/_stcore/health" >/dev/null 2>&1; then
  echo "! Server se nije pokrenuo. Pošalji Claude-u izlaz komande: tail -30 $LOGS/finnews-server.log"
fi
echo ""
echo "✓ Gotovo! FinNews se otvara iz Spotlight-a (Cmd+Space → FinNews) ili iz ~/Applications."
echo "  Portfolio u menu baru:            bash $APP_DIR/swiftbar.sh"
echo "  Telefon (i kad je Mac ugašen):    bash $APP_DIR/deploy_cloud.sh"
echo "  Privremeni link za druge:         bash $APP_DIR/share.sh"
echo "  Widget 📈 je u menu baru gore desno, a obaveštenje stiže svakog jutra u $NOTIFY_HOUR:$(printf %02d $NOTIFY_MINUTE)."
open "$APP"
