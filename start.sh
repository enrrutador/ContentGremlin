#!/usr/bin/env bash
# ContentGremlin — one-command local start (API + Editor)
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "== ContentGremlin =="

need() { command -v "$1" >/dev/null 2>&1 || { echo "Falta: $1"; exit 1; }; }
need python3
need node
need ffmpeg
need ffprobe

if [ ! -f .env ] && [ -f .env.example ]; then
  cp .env.example .env
  echo "Creado .env desde .env.example — editá tus API keys."
fi

if [ ! -d venv ]; then
  echo "Creando venv..."
  python3 -m venv venv
fi
# shellcheck disable=SC1091
source venv/bin/activate
pip install -q -r requirements.txt

if [ ! -d video_editor/node_modules ]; then
  echo "npm install (editor)..."
  (cd video_editor && npm install --silent)
fi

GREMLIN_PORT="${GREMLIN_PORT:-8000}"
EDITOR_PORT="${EDITOR_PORT:-3000}"

echo "Arrancando Gremlin API en :$GREMLIN_PORT ..."
python main.py &
PID_G=$!

echo "Arrancando Editor en :$EDITOR_PORT ..."
(cd video_editor && PORT="$EDITOR_PORT" node server.js) &
PID_E=$!

cleanup() {
  echo "Deteniendo..."
  kill $PID_G $PID_E 2>/dev/null || true
}
trap cleanup EXIT INT TERM

sleep 2
echo ""
echo "  Gremlin API:  http://127.0.0.1:$GREMLIN_PORT"
echo "  Editor:       http://127.0.0.1:$EDITOR_PORT"
echo "  Docs agente:  skills/SKILL.md + video_editor/skills/SKILL.md"
echo "  Producto:     docs/PRODUCT.md"
echo ""
echo "Ctrl+C para detener ambos."
wait
