import logging

import requests
from django.conf import settings

from .transformers import parse_kobo_json

logger = logging.getLogger(__name__)


def get_formserver_uri():
    if settings.KOBO_FORM_SERVER:
        return settings.KOBO_FORM_SERVER
    raise Exception("KOBO_FORM_SERVER not set in settings")


def get_formserver_token():
    if settings.KOBO_FORM_TOKEN:
        return settings.KOBO_FORM_TOKEN
    raise Exception("KOBO_FORM_TOKEN is not set")


def get_server_form(form_name):
    logger.debug(f"Retrieving {form_name} from form server")

    _formserver = get_formserver_uri()
    _token = get_formserver_token()

    assets_url = f"{_formserver}assets/"
    _headers = {"Accept": "application/json", "Authorization": f"Token {_token}"}

    f = requests.get(assets_url, headers=_headers)
    r = f.json()

    if r["count"] < 1:
        logger.debug(f"No results from form server. Check auth token: {assets_url}")
        return None

    m = list(filter(lambda d: d["name"] == form_name, r["results"]))

    available_forms = ",".join([i["name"] for i in r["results"]])

    if len(m) < 1:
        logger.debug(
            f"No result matching {form_name} from server. Available forms: {available_forms}"
        )
        return None

    return m[0]


def get_form_schema(form_name):

    _form = get_server_form(form_name)

    if not _form:
        logger.info(f"get_form_schema got no form return for form: {form_name}")
        return None

    if not "uid" in _form:
        logger.error(
            f"Malformed server return: no field uid in response from form server"
        )
        return None

    _formserver = get_formserver_uri()
    _token = get_formserver_token()
    _formid = _form["uid"]

    asset_url = f"{_formserver}assets/{_formid}"
    _headers = {"Accept": "application/json", "Authorization": f"Token {_token}"}

    f = None

    try:
        f = requests.get(asset_url, headers=_headers)
    except Exception as e:
        logger.error(e)
        return None

    r = f.json()

    if not r or "url" not in r:
        logger.debug(
            f"No or bad result from form server for form {form_name}. Check auth token: {assets_url}"
        )
        return None

    return_schema = None

    try:
        return_schema = parse_kobo_json(r)
    except Exception as e:
        logging.exception(e)
        return None

    return return_schema
