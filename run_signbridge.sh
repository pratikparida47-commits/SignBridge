#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -x .venv/bin/python ]]; then
  echo "Virtual environment not found. Follow README.md setup first." >&2
  exit 1
fi
source .venv/bin/activate
streamlit run app.py
