import os
from urllib.parse import urlparse

from django.conf import settings
from pymongo import MongoClient


def get_mongo_host():
    mongo_host = os.environ.get("MONGO_HOST", default=False)

    if mongo_host:
        return mongo_host

    if settings.MONGO_HOST:
        return settings.MONGO_HOST

    raise Exception("Require MONGO_HOST to be set")


def get_mongo():
    mongo_host_connection = get_mongo_host()

    mongo_connection = MongoClient(mongo_host_connection)

    return mongo_connection


def get_mongo_db(collection_name="instances"):
    mongo_host = get_mongo_host()

    _parsed = urlparse(mongo_host)

    if not _parsed.path:
        raise Exception("MONGO_HOST has no database specified")

    db_name = _parsed.path.lstrip("/")

    c = get_mongo()

    if not hasattr(c, db_name):
        raise Exception(
            f"Not a valid database for this MONGO host ({mongo_host}): {db_name}"
        )

    db = getattr(c, db_name)

    if not hasattr(db, collection_name):
        raise Exception(
            f"Not a valid collection {collection_name} for database {db_name}"
        )

    return getattr(db, collection_name)
