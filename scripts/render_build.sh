#!/usr/bin/env bash
set -euo pipefail
umask 077
cd "$(dirname "$0")/.."
python -m pip install --disable-pip-version-check -r requirements.txt
# Persistent disks are mounted at runtime, not during Render builds.
build_state=$(mktemp -d)
trap 'rm -rf "$build_state"' EXIT
export RILINDJA_STATE_DIR="$build_state"
python manage.py collectstatic --noinput
python manage.py check --deploy --fail-level WARNING
