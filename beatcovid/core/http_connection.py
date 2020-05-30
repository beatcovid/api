import requests as requestslib
from django.conf import settings


def get_connection_pool_option():
    if not hasattr(settings, "HTTP_CONNECTION_POOLING"):
        return False

    if settings.HTTP_CONNECTION_POOLING:
        return settings.HTTP_CONNECTION_POOLING
    return False


def get_connection():
    _use_pool = get_connection_pool_option()
    _requests = None

    if _use_pool:
        _requests = requestslib.Session()
    else:
        _requests = requestslib

    return _requests


http = get_connection()
