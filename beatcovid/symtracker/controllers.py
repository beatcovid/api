import json
import logging
import os
import re
import sys

from beatcovid.api.controllers import get_submission_data, get_user_last_submission

logger = logging.getLogger(__name__)


BASE_PATH = os.path.join(os.path.dirname(__file__), "fixtures")


FIXTURES_FILE = os.path.join(os.path.dirname(__file__), "fixtures", "symptom_tests.json")

# use array index as index
# @TODO eghhhhhhhhh
HEALTH_WARNINGS = ["All is well", "Keep an eye on it", "Call your doctor"]

HEALTH_TRIGGERS = [
    "A moderate cough is an indication of illness",  # cough
    "An indiction of illness",  # sore throat
]

all_symptoms = [
    "aches",
    "cough",
    "diarrhoea",
    "fatigue",
    "feverish",
    "headache",
    "nasal_congestion",
    "nausea",
    "neckpain",
    "noappetite",
    "nobreath",
    "nosleep",
    "nosmell",
    "phlegm",
    "sorethroat",
    "taste",
    "wheezing",
]

respiratory_problems = [
    "cough",
    "nasal_congestion",
    "sorethroat",
    "nobreath",
    "phlegm",
    "wheezing",
]

general_symptoms = [
    "aches",
    "fatigue",
    "feverish",
    "headache",
    "neckpain",
    "nosleep",
    "noappetite",
]

risk_symptoms = ["cough", "sorethroat", "feverish", "nobreath", "fatigue"]

daily_activities = [
    "activities",
    "bed",
    "home",
    "meals",
    "tasks",
    "selfcare",
    "leaveroom",
]

non_risk_symptoms = respiratory_problems + general_symptoms + daily_activities


__is_number = re.compile("^\d+$")
__is_single_number = re.compile("^\d$")


def get_fixture(fixture_name):
    fixture_file_name = os.path.join(BASE_PATH, f"{fixture_name}.json")
    if not os.path.isfile(fixture_file_name):
        raise Exception(f"Fixture {fixture_name} not found")

    fixture = None

    with open(fixture_file_name) as fh:
        fixture = json.load(fh)

    return fixture


def is_number(value):
    if re.match(__is_number, value):
        return True
    return False


def is_single_number(value):
    if re.match(__is_single_number, value):
        return True
    return False


def cast_value_strings(tag):
    """ strips those _0 numbers from the end of values"""
    if type(tag) is str and "_" in tag:
        value, suffix = tag.split("_", 1)
        if is_single_number(suffix):
            return int(suffix)
    return tag


def get_value_label(tag):
    if type(tag) is str and "_" in tag:
        value, suffix = tag.split("_", 1)
        if is_single_number(suffix):
            return value.capitalize()
    return tag


def cast_bool_strings(tag):
    if not type(tag) is str:
        return tag

    if tag in ["none", "no"]:
        return False

    if tag in ["yes"]:
        return True


def get_user_submissions(form_name, user):
    query = {}
    count = None
    sort = {
        "submission_time": -1,
    }

    results = get_submission_data(form_name, query, count=count, sort=sort)

    if not type(results) is list:
        return []

    return results


def get_user_report(user):
    survey = get_user_submissions("beatcovid19now", "9fdbf6f9c4a942da8a1bccff36e5e3f8")

    if survey and type(survey) is list:
        return get_user_report_from_survey(survey[0])
    return None


def parse_symptoms(survey):
    symptoms = {}
    activities = {}
    survey_out = {}

    for field in survey.keys():
        if field.startswith("symptom_"):
            _, symptom = field.split("_", 1)
            symptoms[symptom] = survey[field]
        elif field.startswith("activity_"):
            _, activity = field.split("_", 1)
            activities[activity] = survey[field]

        else:
            survey_out[field] = survey[field]

    survey_out["symptoms"] = symptoms
    survey_out["activities"] = activities

    return survey_out


def get_user_report_from_survey(survey):
    _parsed_survey = {}

    for field in survey.keys():
        _parsed_survey[field] = cast_value_strings(survey[field])

    _parsed_survey = parse_symptoms(_parsed_survey)

    from pprint import pprint

    pprint(_parsed_survey)

    respirotary_problem_score = sum(
        (
            {
                k: _parsed_survey["symptoms"][k]
                for k in _parsed_survey["symptoms"]
                if k in respiratory_problems
            }
        ).values()
    )

    general_sym_score = sum(
        (
            {
                k: _parsed_survey["symptoms"][k]
                for k in _parsed_survey["symptoms"]
                if k in general_symptoms
            }
        ).values()
    )

    activity_score = sum(
        (
            {
                k: _parsed_survey["symptoms"][k]
                for k in _parsed_survey["symptoms"]
                if k in daily_activities
            }
        ).values()
    )

    risk_number = 0

    contact_score = False
    if survey["contact"] in ["yes", "yes_suspected"]:
        contact_score = True

    contact_close_score = False
    if "contact_type" in survey and survey["contact_type"] in [
        "contact_long",
        "close_long",
        "share_long",
        "contact_presymptomatic",
        "contact_work",
    ]:
        contact_close_score = True

    travel_score = False
    if "travel" in survey and survey["travel"] is "yes":
        traven_score = True

    level = ""
    risk = "A"

    report = {
        "level": "",
        "message": "",
        "risk": risk,
        "travel": travel_score,
        "contact": contact_score,
        "contact_close": contact_close_score,
        "scores": {
            "summary": {
                "respirotary": {
                    "value": respirotary_problem_score,
                    "max": len(respiratory_problems) * 4,
                },
                "general": {"value": general_sym_score, "max": len(general_symptoms) * 4},
                "activity": {"value": activity_score, "max": len(daily_activities) * 4},
            }
        },
    }

    report["scores"]["main"] = {
        sym.capitalize(): get_value_label(survey["symptom_" + sym])
        for sym in risk_symptoms
    }

    report["scores"]["other"] = {
        sym.capitalize(): get_value_label(survey["symptom_" + sym])
        for sym in non_risk_symptoms
        if "symptom_" + sym in survey
    }

    return report


def get_user_symptoms(user=None):
    submissions = []

    if not os.path.isfile(FIXTURES_FILE):
        submissions = get_user_submissions("beatcovid19now", user)
        with open(FIXTURES_FILE, "w") as fh:
            json.dump(submissions, fh)

    if not len(submissions):
        with open(FIXTURES_FILE) as fh:
            submissions = json.load(fh)

    logger.debug(submissions)

    tracker = {"submissions": submissions}

    return tracker
