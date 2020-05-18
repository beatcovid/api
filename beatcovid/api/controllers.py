import collections
import json
import logging
import os
import uuid
from datetime import datetime

import redis
import requests as requestslib
from django.conf import settings
from django.utils.translation import get_language_from_request

from beatcovid.core.cache import get_cache, set_cache
from beatcovid.core.mongo import get_mongo_db

from .transformers import parse_kobo_json
from .utils import get_user_agent

logger = logging.getLogger(__name__)
requests = requestslib.Session()


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


def get_submission_count_base():
    if settings.SUBMISSION_COUNT_BASE:
        return settings.SUBMISSION_COUNT_BASE
    return 0


def get_respondent_count_base():
    if settings.RESPONDENT_COUNT_BASE:
        return settings.RESPONDENT_COUNT_BASE
    return 0


def get_server_form_by_name(form_name):
    """
        Get list of forms from server

        @param form_name - name of the form to find
        @returns
    """
    cache_key = "get_server_form_by_name"
    form_id = get_cache(cache_key, form_name)

    if form_id:
        logger.debug("CACHE HIT for {}".format(form_name))
        return form_id

    logger.debug("CACHE MISS for {}".format(form_name))

    logger.debug(f"Retrieving {form_name} from form server")

    _formserver = get_formserver_uri()
    _token = get_formserver_token()

    assets_url = f"{_formserver}assets/"
    _headers = {"Accept": "application/json", "Authorization": f"Token {_token}"}

    # @TODO breakout requests objects to module and cache
    f = requests.get(assets_url, headers=_headers)
    r = f.json()

    if not "count" in r:
        logger.debug(f"No result from form server. Check auth token: {assets_url}")
        return None

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

    set_cache(cache_key, form_name, m[0])

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


def get_form_pk_from_name(form_name):
    """
        Get the kobocat form pk from a form name.

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

    return server_response["formid"]


def get_user_last_submission(form_name, user):
    if not user or not user.id:
        return None

    query = {"user_id": str(user.id)}
    limit = 1
    sort = {
        "_submission_time": -1,
    }

    result = get_submission_data(form_name, query=query, limit=limit, sort=sort)

    if not type(result) is list:
        return None

    if len(result) > 0:
        return collections.OrderedDict(sorted(result[0].items()))

    return None


def get_user_submissions(form_name, user):
    query = {"user_id": str(user.id)}
    sort = {
        "_submission_time": -1,
    }

    results = get_submission_data(form_name, query, sort=sort)

    if not type(results) is list:
        logger.debug(f"No submissions for user: {user.id}")
        return None

    sorted_results = []

    for s in results:
        sorted_results.append(collections.OrderedDict(sorted(s.items())))

    return results


def submission_cast_date(value):

    try:
        value = datetime.strptime(value, "%m/%d/%Y %H:%M:%S").isoformat()
    except Exception as e:
        pass

    return value


def get_form_schema(form_name, request, user):
    """
        Get the form schema from kobo toolbox

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

    last_submission = get_user_last_submission(form_name, user)

    try:
        return_schema = parse_kobo_json(r, request, user, last_submission)
    except Exception as e:
        logging.exception(e)
        return None

    return return_schema


def submit_form(form_name, form_data, user, request):
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

    # filter out the __ fields which are usually labels
    form_data = {k: v for k, v in form_data.items() if not k.startswith("__")}

    _submit_form_data = {}

    # transform geo fields so place id is primary key
    for field, value in form_data.items():
        if type(value) is dict and "geo" in value:
            geo = value["geo"]
            _submit_form_data[field] = geo["place_id"]
            _submit_form_data[field + "_label"] = geo["formatted_address"]
            _submit_form_data[field + "_lat"] = geo["geometry"]["location"]["lat"]
            _submit_form_data[field + "_lng"] = geo["geometry"]["location"]["lng"]
        else:
            _submit_form_data[field] = value

    submission_parcel = {
        "id": formid,
        "submission": _submit_form_data,
    }

    submission_parcel["meta"] = {"instanceID": f"uuid:{_uuid}"}

    _submit_form_data["user_id"] = str(user.id)
    _submit_form_data["language"] = get_language_from_request(request)
    # _submit_form_data["end"] = str(datetime.now().isoformat())
    _submit_form_data["server_version"] = "1.1.0"  # @TODO read this from pyproject.toml
    _submit_form_data["server_env"] = os.environ.get("ENV", default="production")

    if not "session_id" in _submit_form_data:
        _submit_form_data["session_id"] = request.session._get_or_create_session_key()

    if not "user_agent" in _submit_form_data:
        _submit_form_data["user_agent"] = get_user_agent(request)

    try:
        f = requests.post(submission_endpoint, json=submission_parcel, headers=_headers)
    except Exception as e:
        logger.error(e)
        return None

    server_response = f.json()

    return server_response


def get_survey_user_count(form_name="beatcovid19now"):
    q = get_submission_data(form_name, query={}, count=1)

    respondent_count_base = get_respondent_count_base()

    if q and type(q) is dict and "count" in q:
        return int(q["count"]) + respondent_count_base

    return 0 + respondent_count_base


def get_submission_data(form_name, query, limit=None, count=None, sort=None):
    """
        Gets submissoin data for a form

        @param formid - kpi asset id
        @param query - query the data as object with kobocat params
    """
    form_id = get_form_pk_from_name(form_name)

    if not form_id:
        logger.info(f"get_form_id_from_name got no form id for form: {form_name}")
        return None

    _formserver = get_kobocat_uri()
    _token = get_kobocat_token()

    data_endpoint = f"{_formserver}api/v1/data/{form_id}"
    _headers = {"Accept": "application/json", "Authorization": f"Basic {_token}"}

    f = None

    _q = {}

    if query:
        _q["query"] = json.dumps(query)

    if limit:
        _q["limit"] = limit

    if count:
        _q["count"] = count

    if sort:
        _q["sort"] = json.dumps(sort)

    from urllib.parse import quote_plus

    payload_str = "&".join("%s=%s" % (k, quote_plus(str(v))) for k, v in _q.items())

    logger.debug("get_data query: %s %s", data_endpoint, payload_str)

    try:
        f = requests.get(f"{data_endpoint}?{payload_str}", headers=_headers)
    except Exception as e:
        logger.error(e)
        return None

    _resp = None

    try:
        _resp = f.json()
    except Exception as e:
        logger.error("get_data query: %s %s", data_endpoint, payload_str)
        logger.exception(e)
        logger.error("Error parsing response JSON %s".format(e))
        return False

    if not type(_resp) is list:
        _resp = []

    _resp = [
        {
            k: submission_cast_date(v)
            for k, v in i.items()
            if not (k.startswith("_") and not k in ["_id", "_submission_time", "_uuid"])
        }
        for i in _resp
    ]

    return _resp


def kobocat_transform_transport(record):
    SKIP_FIELDS = ["meta/instanceID", "_bamboo_dataset_id", "_attachments"]
    record_out = {}

    for i in record.keys():
        if i.startswith("transport/"):
            _, field = i.split("transport/", 1)
            record_out[field] = record[i]
        elif i in SKIP_FIELDS:
            continue
        else:
            record_out[i.lstrip("_")] = record[i]

    return record_out


def get_stats(form_name):
    """

        get submission stats straight from ongo

        @param form_name - kobo form name
    """

    form_id = get_form_id_from_name(form_name)

    if not form_id:
        logger.info(f"get_form_id_from_name got no form id for form: {form_name}")
        return None

    db = get_mongo_db()

    _filter_total_subs = {}

    submission_count_base = get_submission_count_base()
    submission_count = db.find(_filter_total_subs).count()
    respondents = len(db.distinct("user_id"))

    beatcovid_response = {
        "form": form_name,
        # "submissions_today": server_response["submission_count_for_today"],
        "submissions_raw": submission_count_base + submission_count,
        "submissions": submission_count,
        "respondents": respondents,
        # "submission_last": server_response["last_submission_time"],
        # "date_modified": server_response["date_modified"],
    }

    return beatcovid_response


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

    submission_count_base = get_submission_count_base()

    beatcovid_response = {
        "form": server_response["title"],
        "submissions_today": server_response["submission_count_for_today"],
        "submissions": submission_count_base + server_response["num_of_submissions"],
        "respondents": get_survey_user_count(),
        "submission_last": server_response["last_submission_time"],
        "date_modified": server_response["date_modified"],
    }

    return beatcovid_response
