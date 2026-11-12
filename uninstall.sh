#!/bin/bash
# Uklanja FinNews servise, pokretač i widget. Arhiva ostaje u ~/Library/Application Support/FinNews
UIDN="$(id -u)"
for L in server fetch notify; do
  launchctl bootout "gui/$UIDN/rs.andjiko.finnews.$L" 2>/dev/null || true
  rm -f "$HOME/Library/LaunchAgents/rs.andjiko.finnews.$L.plist"
done
pkill -f "finnews/.venv/bin/streamlit" 2>/dev/null || true
rm -rf "$HOME/Applications/FinNews.app"
rm -f "$(cd "$(dirname "$0")" && pwd)/widgets/swiftbar/finnews.15m.sh"
echo "FinNews uklonjen. Arhivu obriši ručno ako želiš: ~/Library/Application Support/FinNews"
