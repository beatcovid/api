import json
import logging
import os
import re
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

RISK_HEADER = (
    "<h2>Your results today based on the<br>Australian Government recommendations</h2>"
)

RISK_FOOTER = "For up-to-date information follow your national COVID-19 guidelines or look at 'Advice for public' on the <a href='https://www.who.int/emergencies/diseases/novel-coronavirus-2019/advice-for-public' target='_blank'>WHO website</a>."

RISK_LABELS = {
    "A": [
        RISK_HEADER,
        "Report: No or mild symptoms, no recent travel or exposure",
        "Please continue to monitor your wellbeing and complete the Tracker each day.",
        RISK_FOOTER,
    ],
    "B": [
        RISK_HEADER,
        "Report: You reported that you have mild, moderate or severe symptoms and no recent travel or exposure.",
        "Please continue to monitor your symptoms and complete the Tracker each day. If you have serious symptoms such as difficulty breathing, call  your emergency line for urgent medical help. If you would like to talk to someone about your symptoms, contact your local COVID-19 Health Information Line.",
        RISK_FOOTER,
    ],
    "C": [
        RISK_HEADER,
        "Report: You reported that you may have symptoms including shortness of breath (moderate or severe), with no recent travel or exposure.",
        "If you have serious symptoms such as difficulty breathing, call your emergency line for urgent medical help.  If you would like to talk to someone about your symptoms, contact your local COVID-19 Health Information Line. Please continue to monitor your symptoms and complete the Tracker each day.",
        RISK_FOOTER,
    ],
    "D": [
        RISK_HEADER,
        "Report: You reported that you have moderate to severe symptoms and recent travel or exposure.",
        "Contact your local health authority and/or your medical practitioner immediately. If you have serious symptoms such as difficulty breathing, call your emergency line for urgent medical help. Please continue to monitor your symptoms and complete the Tracker each day.",
        RISK_FOOTER,
    ],
    "E": [
        RISK_HEADER,
        "Report: You reported that you have none or mild symptoms and recent travel or exposure.",
        "Follow the advice about isolation and monitoring your health provided to you by your local health authority. Please, continue to monitor your symptoms and complete the Tracker each day.",
        "If you experience worsening symptoms such as difficulty breathing, please seek urgent medical help and make sure you let the health service know that you have recently returned from travel or had exposure to a confirmed or suspected case of COVID-19.",
        RISK_FOOTER,
    ],
    "F": [
        RISK_HEADER,
        "You have reported a positive COVID-19 test result or are awaiting your test results.",
        "Follow the advice about isolation and monitoring your health provided to you by your local health authority. Please, continue to monitor your symptoms and complete the Tracker each day.",
        "If you experience worsening symptoms such as difficulty breathing, please seek urgent medical help and make sure you let the health service know that you have tested positive for COVID-19.",
        "For up-to-date information follow your national COVID-19 guidelines or look at ‘Advice for public’ on <a href='https://www.who.int/emergencies/diseases/novel-coronavirus-2019/advice-for-public'>the WHO website</a>",
    ],
    "FWAITING": [
        RISK_HEADER,
        "You have reported you are awaiting your test results. ",
        "Follow the advice about isolation and monitoring your health provided to you by your local health authority. Please, continue to monitor your symptoms and complete the Tracker each day.",
        "If you experience worsening symptoms such as difficulty breathing, please seek urgent medical help and make sure you let the health service know that you are awaiting your test results.",
        "For up-to-date information follow your national COVID-19 guidelines or look at ‘Advice for public’ on <a href='https://www.who.int/emergencies/diseases/novel-coronavirus-2019/advice-for-public'>the WHO website</a>",
    ],
}


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
            / len(score_fields)
        ),
        1,
    )

    return {"value": score, "max": score_max}


def get_value_dict_for(survey, schema, label):
    _parsed_survey = parse_survey(survey)

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
    risk_score = "A"
    risk_label = None

    symptom_score = get_summary_score(survey, general_symptoms)["value"]
    risk_symptom_score = get_summary_score(survey, risk_symptoms)["value"]

    risk_symptoms_mod_or_severe = [
        i
        for i in (
            {k: survey["symptoms"][k] for k in survey["symptoms"] if k in risk_symptoms}
        ).values()
        if i > 1
    ]
    risk_symptoms_has_mod_or_severe = len(risk_symptoms_mod_or_severe)

    risk_symptoms_none_or_mild = [
        i
        for i in (
            {k: survey["symptoms"][k] for k in survey["symptoms"] if k in risk_symptoms}
        ).values()
        if i <= 1
    ]
    risk_symptoms_has_none_or_mild = len(risk_symptoms_none_or_mild)

    if symptom_score > 0 and not has_contact and not has_travel:
        risk_score = "B"

    elif risk_symptoms_has_mod_or_severe and (not has_close_contact and not has_travel):
        risk_score = "C"

    elif risk_symptoms_has_mod_or_severe and (has_close_contact or has_travel):
        risk_score = "D"

    elif risk_symptoms_has_none_or_mild and (has_contact or has_travel):
        risk_score = "E"

    elif "test_results" in survey and survey["test_result"] == "positive":
        risk_score = "F"

    elif "test_results" in survey and survey["test_result"] == "waiting":
        risk_score = "F"
        risk_label = "FWAITING"

    if not risk_label:
        risk_label = risk_score

    risk_labels_out = []
    if risk_label in RISK_LABELS:
        risk_labels_out = RISK_LABELS[risk_label]

    else:
        logger.error("Could not find risk labels for {}".format(risk_label))

    return {"score": risk_score, "label": risk_labels_out}


def get_user_report_from_survey(surveys, schema=None):
    survey_most_recent = surveys[0]
    _parsed_survey_most_recent = parse_survey(survey_most_recent)

    # invalid survey 3 is a bit arbitary
    if len(survey_most_recent.keys()) < 3:
        return {}

    _scores = []

    for s in surveys:
        _parsed_survey = parse_survey(s)

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

        has_travel = (
            "travel" in survey_most_recent and survey_most_recent["travel"] == "yes"
        )

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
            "level": "",
            "message": "",
            "risk": get_risk_score(
                _parsed_survey_most_recent, has_travel, has_contact, has_contact_close,
            ),
            "travel": has_travel,
            "contact": has_contact,
            "contact_close": has_contact_close,
            "summary": _score_summary,
            "main": get_value_dict_subset_for(s, schema, risk_symptoms),
            "other": get_value_dict_subset_for(s, schema, non_risk_symptoms),
            "activities": get_value_dict_for(s, schema, "activity"),
            "worries": get_value_dict_for(s, schema, "worry"),
        }

        if "version" in _parsed_survey:
            _score["version"] = _parsed_survey["version"]

        survey_date = None
        if "start" in _parsed_survey:
            survey_date = dateparse.parse_datetime("2020-04-17T07:08:27.572Z").strftime(
                "%d-%m-%Y"
            )

            _score["date_day"] = survey_date
            _score["date_started"] = _parsed_survey["start"]

            if "end" in _parsed_survey:
                _score["date_submitted"] = _parsed_survey["end"]

            if "timezone" in _parsed_survey:
                _score["timezone"] = _parsed_survey["timezone"]

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
        "respondents_total": get_survey_user_count(),
        "scores": _scores,
    }

    return report
