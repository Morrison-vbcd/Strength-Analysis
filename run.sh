#!/usr/bin/env bash
# mac / linux 一鍵啟動
set -e
cd "$(dirname "$0")"

if [ ! -x ".venv/bin/python" ]; then
  echo "First run: creating virtual environment ..."
  python3 -m venv .venv
fi

echo "Checking packages (first run may take 1-3 minutes; statsmodels is large) ..."
.venv/bin/python -m pip install -q --disable-pip-version-check -r requirements.txt

echo "Starting app at http://localhost:8501 ..."
.venv/bin/python -m streamlit run app.py --server.headless false
