#!/bin/bash
# FinNews - link za telefon i za druge ljude (profesori, kolege).
# Pokreni:  bash ~/finnews/share.sh      Zaustavi: Ctrl+C
# Dok je ovaj prozor otvoren i Mac uključen, aplikacija je dostupna preko https linka koji se ispiše ispod.
# Preko linka su Portfolio i Podešavanja zaključani PIN-om (postavlja se u aplikaciji: ⚙ → Deljenje i telefon).
set -e
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
PORT=8766
BIN="$APP_DIR/.venv/bin"
[ -x "$BIN/streamlit" ] || { echo "Prvo pokreni instalaciju: bash $APP_DIR/install.sh"; exit 1; }

CF="$(command -v cloudflared || true)"
if [ -z "$CF" ]; then
  CF="$APP_DIR/.venv/bin/cloudflared"
  if [ ! -x "$CF" ]; then
    echo "→ Preuzimam cloudflared (besplatan alat kompanije Cloudflare za bezbedan link, bez naloga)..."
    ARCH="$(uname -m)"; [ "$ARCH" = "arm64" ] && A="arm64" || A="amd64"
    TMP="$(mktemp -d)"
    curl -fsSL "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-$A.tgz" -o "$TMP/cf.tgz"
    tar -xzf "$TMP/cf.tgz" -C "$TMP" && mv "$TMP/cloudflared" "$CF" && chmod +x "$CF"
  fi
fi

echo "→ Pokrećem javnu kopiju aplikacije (lični delovi su iza PIN-a)..."
FINNEWS_PUBLIC=1 "$BIN/streamlit" run "$APP_DIR/app.py" --server.port $PORT --server.address 127.0.0.1 \
  --server.headless true --server.enableCORS false --server.enableXsrfProtection false >/tmp/finnews-share.log 2>&1 &
SPID=$!
trap 'kill $SPID 2>/dev/null; echo; echo "Deljenje je zaustavljeno."' EXIT
sleep 4
echo
echo "════════════════════════════════════════════════════════════════"
echo "  Link se pojavljuje ispod (https://....trycloudflare.com)."
echo "  Otvori ga na telefonu ili ga pošalji drugima."
echo "  Na telefonu: Share → Add to Home Screen, pa radi kao aplikacija."
echo "  Link važi dok je ovaj prozor otvoren; svako pokretanje daje novi link."
echo "════════════════════════════════════════════════════════════════"
echo
"$CF" tunnel --url "http://127.0.0.1:$PORT" 2>&1 | grep --line-buffered -Eo "https://[a-z0-9-]+\.trycloudflare\.com" | while read -r URL; do
  echo "  ➜  $URL"
  command -v pbcopy >/dev/null && printf "%s" "$URL" | pbcopy && echo "     (link je kopiran - Cmd+V da ga nalepiš)"
done
