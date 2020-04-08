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


def get_kobocat_uri():
    if settings.KOBOCAT_API:
        return settings.KOBOCAT_API
    raise Exception("KOBOCAT_API is not set")


def get_kobocat_token():
    if settings.KOBO_FORM_TOKEN:
        return settings.KOBO_FORM_TOKEN
    raise Exception("KOBO_FORM_TOKEN is not set")


def get_server_form(form_name):
    """
        Get list of forms from server

        @param form_name - name of the form to find
        @returns
    """
    logger.debug(f"Retrieving {form_name} from form server")

    _formserver = get_formserver_uri()
    _token = get_formserver_token()

    assets_url = f"{_formserver}assets/"
    _headers = {"Accept": "application/json", "Authorization": f"Token {_token}"}

    # @TODO breakout requests objects to module and cache
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
    """
        Get the form schema from kobo cat

        @param form_name - the name of the form
        @returns parsed form schema JSON
    """

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


def submit_form(formid, submission):
    """
        Submit a form to Kobo via Kobocat

        curl -X POST -d '{"id": "[form ID]", "submission": [the JSON]} http://localhost:8000/api/v1/submissions

        @param formid - kpi asset id
        @param submission - submission form values as JSON
        @returns submission verification body back to client

    """
    # @TODO sanity check formid and submission
    # pass

    _formserver = get_kobocat_uri()
    _token = get_kobocat_token()

    submission_endpoint = f"{_formserver}api/v1/submissions"
    _headers = {"Accept": "application/json", "Authorization": f"Basic {_token}"}

    f = None
    submission_parcel = {
        "id": formid,
        "submission": submission,
    }

    try:
        f = requests.post(submission_endpoint, json=submission_parcel, headers=_headers)
    except Exception as e:
        logger.error(e)
        return None

    server_response = f.json()

    return server_response


def get_submission_data(formid, query=None):
    """
        Gets submissoin data for a form

        @param formid - kpi asset id
        @param query - query the data
    """
    _formserver = get_kobocat_uri()
    _token = get_kobocat_token()

    data_endpoint = f"{_formserver}api/v1/data"
    _headers = {"Accept": "application/json", "Authorization": f"Basic {_token}"}

    f = None
    submission_parcel = {
        "id": formid,
        "submission": submission,
    }

    if query:
        submission_parcel["query"] = query

    try:
        f = requests.post(data_endpoint, json=submission_parcel, headers=_headers)
    except Exception as e:
        logger.error(e)
        return None

    # @TODO catch JSON parsing errors (the server can? something throw back HTML)
    server_response = f.json()

    return server_response


def get_submission_stats(formid):
    """
        Get submission stats for a form such as number of repondents, number
        of submissions, etc.

        @param formid - kpi form id

    """
    # @TODO switch this to using kpi rather than kobocat
    _formserver = get_kobocat_uri()
    _token = get_kobocat_token()

    data_endpoint = f"{_formserver}api/v1/data"
    _headers = {"Accept": "application/json", "Authorization": f"Basic {_token}"}

    f = None
    submission_parcel = {
        "id": formid,
        "submission": submission,
    }

    if query:
        submission_parcel["query"] = query

    try:
        f = requests.post(data_endpoint, json=submission_parcel, headers=_headers)
    except Exception as e:
        logger.error(e)
        return None

    # @TODO catch JSON parsing errors (the server can? something throw back HTML)
    server_response = f.json()

    return server_response
