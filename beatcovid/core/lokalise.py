import json
import logging

import requests

from beatcovid.intl.utils import get_lokalise_project_id, get_lokalise_token

logger = logging.getLogger(__name__)

LOKALISE_BASE_URI = "https://api.lokalise.com/api2/projects/{project_id}/{endpoint}"


class Lokalise:
    session = None
    token = None
    project = None

    def __init__(self):
        self.session = requests.Session()
        self.token = get_lokalise_token()
        self.project = get_lokalise_project_id()

        print(self.token)

        self.session.headers.update({"x-api-token": self.token})

    def keys_list(self):
        req_url = LOKALISE_BASE_URI.format(
            **{"project_id": self.project, "endpoint": "keys"}
        )

        print(req_url)

        resp = self.session.get(
            req_url,
            params={"limit": 5000, "include_translations": 1},
            # headers={"X-Api-Token": self.token},
        )
        # logger.info(resp.json())

        if resp.status_code != 200:
            raise Exception("Error: {}".format(resp))

        return resp.json()
