#!/usr/bin/env sh
set -eu

python -m app.scripts.__init__db
python seed_db.py

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
