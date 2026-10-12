#!/usr/bin/env bash
set -euo pipefail
umask 077
cd "$(dirname "$0")/.."
if [ "${RENDER:-}" = 'true' ]; then
    if [ "${RILINDJA_DEBUG:-0}" != '0' ]; then
        echo 'Render requires RILINDJA_DEBUG=0.' >&2
        exit 1
    fi
    if [ -z "${RILINDJA_DATABASE_URL:-}" ]; then
        echo 'Configure RILINDJA_DATABASE_URL with the private PostgreSQL connection URL.' >&2
        exit 1
    fi
    if [ ! -d /var/data ]; then
        echo 'Mount a Render persistent disk at /var/data before startup.' >&2
        exit 1
    fi
fi
python manage.py migrate --noinput
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-2}" --timeout 60 --access-logfile - --error-logfile -
