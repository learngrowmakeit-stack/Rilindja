#!/usr/bin/env bash
set -euo pipefail
umask 077
cd /workspace/Rilindja
if [ ! -x /workspace/.venvs/rilindja/bin/python ]; then
    python3 -m venv /workspace/.venvs/rilindja
fi
export RILINDJA_DEBUG="${RILINDJA_DEBUG:-1}"
/workspace/.venvs/rilindja/bin/python -m pip install --disable-pip-version-check -r requirements.txt
/workspace/.venvs/rilindja/bin/python manage.py migrate --noinput
/workspace/.venvs/rilindja/bin/python manage.py check
