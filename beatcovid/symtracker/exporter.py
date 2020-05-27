import csv
import json
import os
from collections import OrderedDict
from pprint import pprint

from .controllers import (
    all_symptoms,
    get_risk_score,
    get_user_report_from_survey,
    non_risk_symptoms,
    risk_symptoms,
)
from .tests import get_fixture

CSV_PATH = os.path.join(os.getcwd(), "symtracker_export.csv")

SYMPTOM_SCORES = ["none_0", "some_1", "moderate_2", "severe_3"]
RISK_SYMPTOM_SCORES = ["none_0", "some_1", "moderate_2", "severe_3"]
CONTACT_SCORES = [
    "anyone",
    "small_circle",
    "household_plus",
    "household_only",
    "healthcare_only",
    "no_one",
]
CONTACT_TYPE = [
    "contact_long",
    "contact_short",
    "share_long",
    "share_short",
    "contact_presymptomatic",
    "contact_work",
]
COVID_CONTACT_SCORES = ["yes_confirmed", "yes_suspect", "no"]
TESTED_SCORES = ["yes_tested", "yes_not", "no"]


def export_test():
    f = get_fixture("submission_single")

    entries = []

    for symptom_score in SYMPTOM_SCORES:
        for risk_symptom_score in RISK_SYMPTOM_SCORES:
            for travel in ["yes", "no"]:
                for contact in COVID_CONTACT_SCORES:
                    for tested in TESTED_SCORES:
                        for tested_result in ["negative", "positive", "waiting"]:
                            for contact_type in CONTACT_TYPE:
                                result = {}

                                if tested == "no" and tested_result in [
                                    "positive",
                                    "waiting",
                                ]:
                                    continue

                                if contact == "no" and contact_type != "contact_long":
                                    continue

                                if contact == "no":
                                    contact_type = ""

                                for s in risk_symptoms:
                                    f["symptom_" + s] = risk_symptom_score

                                for si in non_risk_symptoms:
                                    f["symptom_" + si] = symptom_score

                                result["tested"] = f["tested"] = tested
                                result["tested_result"] = f[
                                    "tested_result"
                                ] = tested_result
                                result["contact"] = f["contact"] = contact
                                result["travel"] = f["travel"] = travel
                                result["contact_type"] = f["contact_type"] = contact_type

                                r = get_user_report_from_survey([f])

                                for s in all_symptoms:
                                    result["symptom_" + s] = f["symptom_" + s]

                                scores = r["scores"][0]

                                result = {
                                    **result,
                                    **{
                                        "score_acvitity": scores["summary"]["activity"][
                                            "value"
                                        ],
                                        "score_general": scores["summary"]["general"][
                                            "value"
                                        ],
                                        "score_respiratory": scores["summary"][
                                            "respiratory"
                                        ]["value"],
                                        "score_risk": r["scores"][0]["risk"]["score"],
                                    },
                                }

                                result["score_risk_label"] = r["scores"][0]["risk"][
                                    "label"
                                ]

                                # pprint(result)
                                entries.append((result))

    with open(CSV_PATH, "w", newline="") as fh:
        # fieldnames = entries[0].keys()
        non_risk_symptoms_fieldnames = ["symptom_" + i for i in non_risk_symptoms]
        risk_symptoms_fieldnames = ["symptom_" + i for i in risk_symptoms]
        other_fields = [
            "tested",
            "tested_result",
            "travel",
            "contact",
            "contact_type",
        ]
        result_field_names = [
            "score_acvitity",
            "score_general",
            "score_respiratory",
            "score_risk",
            "score_risk_label",
        ]

        fieldnames = (
            non_risk_symptoms_fieldnames
            + risk_symptoms_fieldnames
            + other_fields
            + result_field_names
        )

        writer = csv.DictWriter(fh, fieldnames=fieldnames)

        writer.writeheader()
        for e in entries:
            writer.writerow(e)

    print("Wrote file {}".format(CSV_PATH))
