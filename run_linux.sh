
#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
command -v python3 >/dev/null 2>&1 || { echo "Python 3.10+ is required."; exit 1; }
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
