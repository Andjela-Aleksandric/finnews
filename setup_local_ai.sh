#!/bin/bash
# Besplatni lokalni AI za FinNews (Ollama). Radi na tvom Mac-u, bez ključa i bez slanja podataka napolje.
set -e
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
RAM_GB=$(( $(sysctl -n hw.memsize) / 1073741824 ))
MODEL="gemma3:12b"
if [ "$RAM_GB" -lt 16 ]; then MODEL="gemma3:4b"; fi
echo "→ Mac ima ${RAM_GB} GB RAM - koristim model $MODEL"
if ! command -v ollama >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    echo "→ Instaliram Ollama..."
    brew install ollama
  else
    echo "Instaliraj Ollama sa https://ollama.com/download (prevuci u Applications, pokreni jednom), pa ponovo pokreni ovu skriptu."
    exit 1
  fi
fi
brew services start ollama >/dev/null 2>&1 || (nohup ollama serve >/dev/null 2>&1 &)
for i in $(seq 1 20); do curl -s http://localhost:11434/api/tags >/dev/null 2>&1 && break; sleep 1; done
echo "→ Preuzimam model (jednom, nekoliko GB - može da potraje)..."
ollama pull "$MODEL"
"$APP_DIR/.venv/bin/python" -c "import sys; sys.path.insert(0, '$APP_DIR'); import ai; c = ai.load_config(); c['ollama_model'] = '$MODEL'; ai.save_config(c)"
echo "✓ Lokalni AI je spreman. Osveži FinNews - dnevni brief, analize studija i predlozi tema sada rade bez ključa."
