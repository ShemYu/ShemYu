#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

uv run --locked python -m src.main --locale ja --select ly_agent --pdf
uv run --locked python -m src.main --locale ja --select ly_platform --pdf
