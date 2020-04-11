#!/bin/sh

set -e

# activate venv
. .venv/bin/activate

python manage.py collectstatic

exec "$@"
