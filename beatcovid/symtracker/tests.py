import json
import logging
import os
from pprint import pprint

from django.test import TestCase

from beatcovid.symtracker.controllers import (cast_bool_strings,
                                              get_user_report_from_survey)

BASE_PATH = os.path.join(os.path.dirname(__file__), "fixtures")


def get_fixture(fixture_name):
    fixture_file_name = os.path.join(BASE_PATH, f"{fixture_name}.json")
    if not os.path.isfile(fixture_file_name):
        raise Exception(f"Fixture {fixture_name} not found")

    fixture = None

    with open(fixture_file_name) as fh:
        fixture = json.load(fh)

    return fixture


class FromReadableDictToDictTestCase(TestCase):

# class ValueParseTestCase(TestCase):
#     def setUp(self):
#         # self.data = get_fixture("all_form_values")
#         pass

#     def test_value_parsing(self):
#         pass
#         # for f in fixture
#         # self.assertEqual(f, "f.value")


class SymptomTrackerSingleEntryTestCase(TestCase):
    def setUp(self):
        self.data = get_fixture("submission_single")

    def test_value_parsing(self):
        logging.debug(self.data)

        report = get_user_report_from_survey(self.data)

        pprint(report)
        # for f in fixture
        # self.assertEqual(f, "f.value")
