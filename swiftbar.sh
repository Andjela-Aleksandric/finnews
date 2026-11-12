#!/bin/bash
# FinNews u menu baru (SwiftBar): trenutna vrednost portfolija, pozicije i najvažnije vesti.
# Pokreni:  bash ~/finnews/swiftbar.sh
set -e
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
VPY="$APP_DIR/.venv/bin/python"
[ -x "$VPY" ] || { echo "Prvo pokreni instalaciju: bash $APP_DIR/install.sh"; exit 1; }
PLUG="$APP_DIR/widgets/swiftbar"; mkdir -p "$PLUG"; rm -f "$PLUG"/finnews.*.sh
cat > "$PLUG/finnews.5m.sh" <<EOT
#!/bin/bash
# <swiftbar.hideRunInTerminal>true</swiftbar.hideRunInTerminal>
# <swiftbar.hideDisablePlugin>true</swiftbar.hideDisablePlugin>
exec "$VPY" "$APP_DIR/widgets/menubar.py"
EOT
chmod +x "$PLUG/finnews.5m.sh"
if [ ! -d "/Applications/SwiftBar.app" ] && [ ! -d "$HOME/Applications/SwiftBar.app" ]; then
  if command -v brew >/dev/null 2>&1; then echo "→ Instaliram SwiftBar..."; brew install --cask swiftbar
  else echo "Preuzmi SwiftBar sa https://swiftbar.app, prevuci ga u Applications i pokreni ponovo ovu komandu."; exit 1; fi
fi
killall SwiftBar 2>/dev/null || true
defaults write com.ameba.SwiftBar PluginDirectory "$PLUG"
defaults write com.ameba.SwiftBar MakePluginExecutable -bool true
sleep 1; open -a SwiftBar
sleep 3; open -g "swiftbar://refreshallplugins" 2>/dev/null || true
echo ""
echo "✓ Gotovo - gore desno u menu baru je 📈 sa vrednošću portfolija (osvežava se na 5 minuta)."
echo "  Ovako trenutno izgleda:"
echo "────────────────────────────────────────"
"$VPY" "$APP_DIR/widgets/menubar.py" 2>/dev/null | sed -E 's/ \|.*$//' | head -24
