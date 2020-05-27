import csv
import json
import os
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


def export_test():
    f = get_fixture("submission_single")

    entries = []

    for i in range(0, 3):
        for x in range(0, 3):
            for s in risk_symptoms:
                f["symptom_" + s] = i

            for s in non_risk_symptoms:
                f["symptoms_" + s] = x

            r = get_user_report_from_survey([f])

            result = {}

            for s in all_symptoms:
                result["symptom_" + s] = f["symptom_" + s]

            scores = r["scores"][0]

            result = {
                **result,
                **{
                    "score_racvitity": scores["summary"]["activity"]["value"],
                    "score_rgeneral": scores["summary"]["general"]["value"],
                    "score_rrespiratory": scores["summary"]["respiratory"]["value"],
                    "score_risk": r["scores"][0]["risk"]["score"],
                },
            }

            # pprint(result)
            entries.append(result)

    with open(CSV_PATH, "w", newline="") as fh:
        fieldnames = entries[0].keys()
        writer = csv.DictWriter(fh, fieldnames=fieldnames)

        writer.writeheader()
        for e in entries:
            writer.writerow(e)

    print("Wrote file {}".format(CSV_PATH))
