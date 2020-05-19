from django.conf import settings


def get_lokalise_token():
    if settings.LOKALISE_TOKEN:
        return settings.LOKALISE_TOKEN
    raise Exception("LOKALISE_TOKEN not set")


def get_lokalise_project_id():
    if settings.LOKALISE_PROJECT_ID:
        return settings.LOKALISE_PROJECT_ID
    raise Exception("LOKALISE_PROJECT_ID not set")
