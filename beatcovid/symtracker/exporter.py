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


def export_test():
    f = get_fixture("submission_single")

    entries = []

    for symptom_score in SYMPTOM_SCORES:
        for risk_symptom_score in RISK_SYMPTOM_SCORES:
            for travel in ["yes", "no"]:
                result = {}

                for s in risk_symptoms:
                    f["symptom_" + s] = risk_symptom_score

                for si in non_risk_symptoms:
                    f["symptom_" + si] = symptom_score

                result["travel"] = f["travel"] = travel

                r = get_user_report_from_survey([f])

                for s in all_symptoms:
                    result["symptom_" + s] = f["symptom_" + s]

                scores = r["scores"][0]

                result = {
                    **result,
                    **{
                        "score_acvitity": scores["summary"]["activity"]["value"],
                        "score_general": scores["summary"]["general"]["value"],
                        "score_respiratory": scores["summary"]["respiratory"]["value"],
                        "score_risk": r["scores"][0]["risk"]["score"],
                    },
                }

                # pprint(result)
                entries.append(OrderedDict(result))

    with open(CSV_PATH, "w", newline="") as fh:
        # fieldnames = entries[0].keys()
        non_risk_symptoms_fieldnames = ["symptom_" + i for i in non_risk_symptoms]
        risk_symptoms_fieldnames = ["symptom_" + i for i in risk_symptoms]
        other_fields = ["travel"]
        result_field_names = [
            "score_acvitity",
            "score_general",
            "score_respiratory",
            "score_risk",
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
