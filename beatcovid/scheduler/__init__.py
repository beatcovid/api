# pylint: disable=invalid-name
import os

from django.conf import settings
from huey import PriorityRedisHuey
from redis import ConnectionPool

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "beatcovid.settings.dev")

pool = ConnectionPool(host="redis", port=6379, max_connections=100)

scheduler = PriorityRedisHuey(name="beatcovid", utc=True, connection_pool=pool)
