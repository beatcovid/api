import logging
import uuid

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
    if settings.KOBOCAT_CREDENTIALS:
        return settings.KOBOCAT_CREDENTIALS
    raise Exception("KOBOCAT_CREDENTIALS is not set")


def get_server_form_by_name(form_name):
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


def get_form_id_from_name(form_name):
    form = get_server_form_by_name(form_name)

    if not type(form) is dict:
        logger.error(f"Bad response when getting form id for name {form_name}")
        return None

    if not "uid" in form:
        logger.error(
            f"Malformed server return: no field uid in response from form server"
        )
        return None

    return form["uid"]


def get_form_schema(form_name, request=None):
    """
        Get the form schema from kobo cat

        @param form_name - the name of the form
        @returns parsed form schema JSON
    """

    formid = get_form_id_from_name(form_name)

    if not formid:
        logger.info(f"get_form_id_from_name got no form id for form: {form_name}")
        return None

    _formserver = get_formserver_uri()
    _token = get_formserver_token()

    asset_url = f"{_formserver}assets/{formid}"
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
        return_schema = parse_kobo_json(r, request)
    except Exception as e:
        logging.exception(e)
        return None

    return return_schema


def submit_form(form_name, form_data):
    """
        Submit a form to Kobo via Kobocat

        curl -X POST -d '{"id": "[form ID]", "submission": [the JSON]} http://localhost:8000/api/v1/submissions

        @param form_name - kpi asset id
        @param submission - submission form values as JSON
        @returns submission verification body back to client

    """
    # @TODO sanity check form_name and submission
    # pass
    formid = get_form_id_from_name(form_name)

    if not formid:
        logger.info(f"get_form_id_from_name got no form id for form: {form_name}")
        return None

    _formserver = get_kobocat_uri()
    _token = get_kobocat_token()

    submission_endpoint = f"{_formserver}api/v1/submissions"
    _headers = {"Accept": "application/json", "Authorization": f"Basic {_token}"}
    _uuid = uuid.uuid4()

    f = None
    submission_parcel = {
        "id": formid,
        "submission": {"transport": form_data, "meta": {"instanceID": f"uuid:{_uuid}"},},
    }

    try:
        f = requests.post(submission_endpoint, json=submission_parcel, headers=_headers)
    except Exception as e:
        logger.error(e)
        return None

    server_response = f.json()

    logger.debug(server_response)

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


def get_submission_stats(form_name):
    """
        Get submission stats for a form such as number of repondents, number
        of submissions, etc.

        @param formid - kpi form id

    """
    # @TODO switch this to using kpi rather than kobocat

    form_id = get_form_id_from_name(form_name)

    if not form_id:
        logger.info(f"get_form_id_from_name got no form id for form: {form_name}")
        return None

    _formserver = get_kobocat_uri()
    _token = get_kobocat_token()

    data_endpoint = f"{_formserver}api/v1/forms"
    _headers = {"Accept": "application/json", "Authorization": f"Basic {_token}"}

    request_paramaters = {"id_string": form_id}

    f = None

    try:
        f = requests.get(data_endpoint, params=request_paramaters, headers=_headers)
    except Exception as e:
        logger.error(e)
        return None

    # @TODO catch JSON parsing errors (the server can? something throw back HTML)
    server_response = f.json()

    if not type(server_response) is list:
        return None

    server_response = server_response[0]

    beatcovid_response = {
        "form": server_response["title"],
        "submissions_today": server_response["submission_count_for_today"],
        "submissions": server_response["num_of_submissions"],
        "submission_last": server_response["last_submission_time"],
        "date_modified": server_response["date_modified"],
    }

    return beatcovid_response
