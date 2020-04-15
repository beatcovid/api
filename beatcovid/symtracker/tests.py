import json
import logging
import os
from pprint import pprint

from django.test import TestCase

from beatcovid.symtracker.controllers import (
    cast_bool_strings,
    get_fixture,
    get_user_report_from_survey,
)

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
        self.data = get_fixture("single_test")

    def test_value_parsing(self):
        logging.debug(self.data)

        report = get_user_report_from_survey(self.data)

        pprint(report)
        # for f in fixture
        # self.assertEqual(f, "f.value")
