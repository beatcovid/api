#!/bin/sh

set -e

# activate venv
. .venv/bin/activate

exec "$@"
