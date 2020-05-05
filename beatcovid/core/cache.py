import json
from datetime import datetime, timedelta

import redis
from django.conf import settings


def get_redis_url():
    if settings.REDIS_URL:
        return settings.REDIS_URL
    raise Exception("REDIS_URL not set in settings please set it.")


def get_redis():
    r = redis.Redis.from_url(settings.REDIS_URL)
    return r


def set_cache(name, key, value, ttl=None):
    r = get_redis()

    serialised = None

    try:
        serialised = json.dumps(value)
    except Exception:
        logger.error(f"cache.get Error serializing for {name} {value}")
        return None

    success = r.hset(name, key, serialised)

    if not ttl:
        ttl = 15

    ttl_dtime = timedelta(minutes=ttl)
    r.expire(name, ttl_dtime)

    return success


def get_cache(name, key):
    r = get_redis()

    serialised = r.hget(name, key)

    if not serialised:
        return False

    try:
        value = json.loads(serialised)
    except Exception:
        logger.error(f"cache.get Error deserializing for {name} {value}")
        return None

    return value
