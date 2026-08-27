#!/usr/bin/env bash
# Live-compose the two LINE Yahoo Japanese 職務経歴書.
# Requires OPENAI_API_KEY in the environment or .env
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -z "${OPENAI_API_KEY:-}" && -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi
if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "OPENAI_API_KEY is required for the live compose path." >&2
  exit 1
fi

DEST="artifacts/ly-yahoo-jp-20260827"
mkdir -p "$DEST"

for name in ly_platform_jp ly_agent_jp; do
  uv run --locked --extra tailoring python -m src.main \
    "$DEST/jds/${name}.txt" \
    --language ja \
    --output-name "$name"
  cp -f "output/tailored/${name}.md" "$DEST/"
  cp -f "output/tailored/${name}.html" "$DEST/"
  cp -f "output/tailored/${name}_bible.html" "$DEST/"
  cp -f "output/tailored/${name}.pdf" "$DEST/"
done

echo "Wrote PDFs/HTML/MD under $DEST"
