#!/usr/bin/env bash
set -euo pipefail

# Move to repo root
cd "$(dirname "$0")"

# Select base Python: prefer python3, then python
choose_python() {
  if command -v python3 >/dev/null 2>&1; then
    echo "python3"
    return
  fi
  if command -v python >/dev/null 2>&1; then
    echo "python"
    return
  fi
  echo "Error: Python 3 not found. Install from https://www.python.org/downloads/macos/ or via Homebrew: brew install python" >&2
  exit 1
}

PY=$(choose_python)

# Create venv if missing
if [[ ! -d .venv ]]; then
  "$PY" -m venv .venv
fi

VENV_PY=".venv/bin/python"
if [[ ! -x "$VENV_PY" ]]; then
  echo "Error: virtual environment appears incomplete: $VENV_PY not found. Try removing .venv and re-running." >&2
  exit 1
fi

# Upgrade pip inside the venv (non-fatal)
if ! "$VENV_PY" -m pip install --upgrade pip; then
  echo "Warning: pip upgrade failed; continuing" >&2
fi

# Install requirements if file exists and is non-empty
REQ="requirements.txt"
if [[ -f "$REQ" ]]; then
  if [[ -s "$REQ" ]]; then
    # Install requirements (non-fatal)
    if ! "$VENV_PY" -m pip install -r "$REQ"; then
      echo "Warning: requirements install failed; continuing" >&2
    fi
  else
    echo "requirements.txt is empty; skipping install"
  fi
else
  echo "requirements.txt not found; skipping install"
fi

# Verify Tk availability (tkinter)
if ! "$VENV_PY" -c 'import tkinter as _tk' >/dev/null 2>&1; then
  echo "Error: Tkinter (Tk) is not available in this Python environment." >&2
  echo "Install a Python build with Tk support. Options:" >&2
  echo "  - Install Python from python.org (includes Tk)." >&2
  echo "  - Or install via Homebrew: brew install python" >&2
  echo "Then remove .venv and re-run this script." >&2
  exit 1
fi

# Launch the GUI using the venv's Python
exec "$VENV_PY" "main.py"
