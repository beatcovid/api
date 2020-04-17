import json
import logging
import os
import re
import string
import sys

from django.utils import dateparse

from beatcovid.api.controllers import (
    get_form_schema,
    get_submission_data,
    get_survey_user_count,
    get_user_last_submission,
    get_user_submissions,
)

logger = logging.getLogger(__name__)


# use array index as index
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

non_risk_symptoms = [s for s in all_symptoms if not s in risk_symptoms]

risk_scores = list([i for i in string.ascii_uppercase[:6]])

RISK_LABELS = []

__is_number = re.compile("^\d+$")
__is_single_number = re.compile("^\d$")


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
    if type(tag) is dict:
        logger.debug(tag)

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


def cast_strings_to_bool(tag):
    if not type(tag) is str:
        return tag

    if tag in ["none", "no"]:
        return False

    if tag in ["yes"]:
        return True

    return tag


def get_user_report(user, request):
    surveys = get_user_submissions("beatcovid19now", user)
    schema = get_form_schema("beatcovid19now", request, user)

    if surveys and type(surveys) is list:
        return get_user_report_from_survey(surveys, schema)

    return None


def parse_survey(survey):
    """ make more sense of the survey """

    symptoms = {}
    activities = {}
    worry = {}
    userdetails = {}
    survey_out = {}
    face_contact = {}
    feeling = {}
    contact = {}

    for field in survey.keys():
        value = cast_value_strings(survey[field])
        value = cast_strings_to_bool(value)

        if field.startswith("symptom_"):
            _, symptom = field.split("_", 1)
            symptoms[symptom] = value
        elif field.startswith("activity_"):
            _, activity = field.split("_", 1)
            activities[activity] = value
        elif field.startswith("worry_"):
            _, wo = field.split("_", 1)
            worry[wo] = value
        elif field.startswith("userdetail_"):
            _, detail = field.split("_", 1)
            userdetails[detail] = value
        elif field.startswith("feeling_"):
            _, detail = field.split("_", 1)
            feeling[detail] = value
        elif field.startswith("contact_"):
            _, detail = field.split("_", 1)
            contact[detail] = value
        elif field.startswith("face_contact_"):
            _, _, c = field.split("_", 2)
            face_contact[c] = value
        else:
            survey_out[field] = value

    survey_out["symptoms"] = symptoms
    survey_out["activity"] = activities
    survey_out["worry"] = worry
    survey_out["user_detail"] = userdetails
    survey_out["face_contact_details"] = face_contact
    survey_out["feeling"] = feeling
    survey_out["contact_details"] = contact

    return survey_out


def get_label_for_field(field, schema):
    if not schema:
        return field

    if field in schema["labels"]:
        return schema["labels"][field]

    return field


def get_summary_score(survey, score_fields, key="symptoms"):

    # for now the max score is just the number of fields
    # score_max = len(score_fields)
    score_max = 3

    # for now score is just average of the fields
    score = round(
        (
            sum(({k: survey[key][k] for k in survey[key] if k in score_fields}).values())
            / score_max
        ),
        1,
    )

    return {"value": score, "max": score_max}


def get_value_dict_for(survey, schema, label):
    _parsed_survey = parse_survey(survey)

    # logger.debug(label)
    # logger.debug(survey)
    logger.debug(_parsed_survey)

    if not label in _parsed_survey:
        return {}

    return {
        get_label_for_field(label + "_" + sym, schema): get_value_label(
            survey[label + "_" + sym]
        )
        for sym in _parsed_survey[label].keys()
        if sym in _parsed_survey[label]
    }


def get_value_dict_subset_for(survey, schema, symptom_list):
    return {
        get_label_for_field("symptom_" + sym, schema): get_value_label(
            survey["symptom_" + sym]
        )
        for sym in symptom_list
        if "symptom_" + sym in survey
    }


def get_risk_score(survey, has_travel, has_contact, has_contact_close):
    risk_score = 0

    if has_travel:
        risk_score += 1

    if has_contact:
        risk_score += 1

    if has_contact_close:
        risk_score += 1

    if survey["symptoms"]["nobreath"] >= 2:
        risk_score += 2

    if risk_score >= len(risk_scores):
        risk_score = len(risk_scores) - 1

    return risk_scores[risk_score]


def get_user_report_from_survey(surveys, schema=None):
    survey_most_recent = surveys[0]
    _parsed_survey_most_recent = parse_survey(survey_most_recent)

    # invalid survey 3 is a bit arbitary
    if len(survey_most_recent.keys()) < 3:
        return {}

    _scores = []
    have_dates = []

    for s in surveys:
        _parsed_survey = parse_survey(s)

        # summary scores
        respirotary_problem_score = get_summary_score(
            _parsed_survey, respiratory_problems
        )
        general_symptom_score = get_summary_score(_parsed_survey, general_symptoms)
        activity_score = get_summary_score(
            _parsed_survey, daily_activities, key="activity"
        )

        # list of return values
        _score_summary = {
            "respiratory": respirotary_problem_score,
            "general": general_symptom_score,
            "activity": activity_score,
        }

        _score = {
            "summary": _score_summary,
            "main": get_value_dict_subset_for(s, schema, risk_symptoms),
            "other": get_value_dict_subset_for(s, schema, non_risk_symptoms),
            "activities": get_value_dict_for(s, schema, "activity"),
            "worries": get_value_dict_for(s, schema, "worry"),
        }

        survey_date = None
        if "start" in _parsed_survey:
            survey_date = dateparse.parse_datetime("2020-04-17T07:08:27.572Z").strftime(
                "%d-%m-%Y"
            )
            have_dates.append(survey_date)

            _score["date"] = survey_date
            _scores.append(_score)

    has_contact = survey_most_recent["contact"] in [
        "yes",
        "yes_suspected",
        "yes_confirmed",
    ]

    has_contact_close = "contact_type" in survey_most_recent and survey_most_recent[
        "contact_type"
    ] in [
        "contact_long",
        "close_long",
        "share_long",
        "contact_presymptomatic",
        "contact_work",
    ]

    has_travel = "travel" in survey_most_recent and survey_most_recent["travel"] == "yes"

    report = {
        "level": "",
        "message": "",
        "risk": get_risk_score(
            _parsed_survey_most_recent, has_travel, has_contact, has_contact_close
        ),
        "travel": has_travel,
        "contact": has_contact,
        "contact_close": has_contact_close,
        "schema_version": survey_most_recent["version"],
        "date_started": survey_most_recent["start"],
        "date_submitted": survey_most_recent["end"],
        "app_version": "1.1.0",
        "total_participants": get_survey_user_count(),
        "scores": _scores,
    }

    return report
