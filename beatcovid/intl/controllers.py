import glob
import json
import logging
import os
from pprint import pprint

import polib
import requests
from django.core.management.base import CommandError
from django.core.management.utils import find_command, is_ignored_path

from beatcovid.api.controllers import (
    get_form_id_from_name,
    get_formserver_token,
    get_formserver_uri,
)

logger = logging.getLogger(__name__)


def find_locale_paths():
    ignore_patterns = set([".venv/*"])

    basedirs = [os.path.join("conf", "locale"), "locale"]

    if os.environ.get("DJANGO_SETTINGS_MODULE"):
        from django.conf import settings

        basedirs.extend(settings.LOCALE_PATHS)

    # Walk entire tree, looking for locale directories
    for dirpath, dirnames, filenames in os.walk(".", topdown=True):
        for dirname in dirnames:
            if is_ignored_path(
                os.path.normpath(os.path.join(dirpath, dirname)), ignore_patterns
            ):
                dirnames.remove(dirname)
            elif dirname == "locale":
                basedirs.append(os.path.join(dirpath, dirname))

    # Gather existing directories.
    basedirs = set(map(os.path.abspath, filter(os.path.isdir, basedirs)))

    if not basedirs:
        raise CommandError(
            "This script should be run from the Django Git "
            "checkout or your project or app tree, or with "
            "the settings module specified."
        )

    # Build locale list
    locales = []
    for basedir in basedirs:
        # default en as base
        locale_dirs = filter(os.path.isdir, glob.glob("%s/en" % basedir))
        locales.extend(map(os.path.basename, locale_dirs))

    locations = []

    for basedir in basedirs:
        if locales:
            dirs = [os.path.join(basedir, l, "LC_MESSAGES") for l in locales]
        else:
            dirs = [basedir]
        for ldir in dirs:
            for dirpath, dirnames, filenames in os.walk(ldir):
                locations.extend((dirpath, f) for f in filenames if f.endswith(".po"))

    return locations


def parse_locales(locations):
    locs = set()
    msgstrings = []

    for i, (dirpath, f) in enumerate(locations):
        locs.add(os.path.join(dirpath, f))

    for po_path in locs:
        po = polib.pofile(po_path)
        print(f"opening {po_path}")
        valid_entries = [e for e in po if not e.obsolete]
        for entry in valid_entries:
            key = po_to_lokalise(entry)
            msgstrings.append(key)

    return msgstrings


def po_to_lokalise(poentry):
    floc = []

    for (f, l) in poentry.occurrences:
        floc.append({"comment": "{}:{}".format(f, l)})

    if poentry.comment:
        floc.append({"comment": poentry.comment})

    return {
        "key_name": poentry.msgid,
        "comments": floc,
        "platforms": ["web"],
        "tags": ["api"],
        "translations": [{"language_iso": "en", "translation": poentry.msgstr}],
    }


def extract_messages():
    locations = find_locale_paths()
    msgstrings = parse_locales(locations)

    return msgstrings


def update_keys(lokalise, messages):
    keys_to_add = []
    keys_to_update = []

    keys = lokalise.keys_list()

    key_ids = [k["key_name"]["web"] for k in keys]

    for message in messages:
        _id = message["key_name"]
        if _id in key_ids:
            print(f"lokalise has key {_id}")
            message["key_id"] = list(filter(lambda x: x["key_name"]["web"] == _id, keys))[
                0
            ]["key_id"]
            keys_to_update.append(message)
        else:
            print(f"lokalise does not have key {_id}")
            keys_to_add.append(message)

    if len(keys_to_update) > 0:
        lokalise.keys_update(keys_to_update)

    if len(keys_to_add) > 0:
        lokalise.keys_add(keys_to_add)


def schema_messages(l):
    keys = l.keys_list("survey")

    translations = {}

    for key in keys:
        if not "key_name" in key:
            continue

        for translation in key["translations"]:
            iso = translation["language_iso"].lower()

            if not iso in translations:
                translations[iso] = {}

            key_name = key["key_name"]["web"]

            if len(translation["translation"]) > 0 and translation["words"] > 0:
                translations[iso][key_name] = translation["translation"]

    save_dir = os.path.join(os.getcwd(), "beatcovid", "api")

    if not os.path.isdir(save_dir):
        raise Exception("Could not find path {}".format(save_dir))

    save_path = os.path.join(save_dir, "translations.json")

    with open(save_path, "w+") as fh:
        json.dump(translations, fh, indent=4)

    return None


def get_form_schema(form_name):
    """
        Get the form schema from kobo toolbox

        @param form_name - the name of the form
        @returns parsed form schema JSON
    """

    formid = get_form_id_from_name(form_name)

    if not formid:
        logger.info(f"get_form_id_from_name got no form id for form: {form_name}")
        return None

    _formserver = get_formserver_uri()
    _token = get_formserver_token()

    asset_url = f"{_formserver}assets/{formid}"
    _headers = {"Accept": "application/json", "Authorization": f"Token {_token}"}

    f = None

    try:
        f = requests.get(asset_url, headers=_headers)
    except Exception as e:
        logger.error(e)
        return None

    r = f.json()

    if not r or "url" not in r:
        logger.debug(
            f"No or bad result from form server for form {form_name}. Check auth token: {asset_url}"
        )
        return None

    return r


def kobo_to_lokalise(kobo):
    floc = []

    return {
        "key_name": kobo["key_name"],
        "platforms": ["web"],
        "tags": ["survey"],
        "translations": [{"language_iso": "en", "translation": kobo["translation"]}],
    }


def update_survey_keys(lokalise, formname="beatcovid19now"):
    keys_to_add = []
    keys_to_update = []

    keys = lokalise.keys_list(tags="survey")

    key_ids = [k["key_name"]["web"] for k in keys]

    schema = get_form_schema(formname)

    choices = schema["content"]["choices"]
    survey = schema["content"]["survey"]

    survey_messages = []

    for i in survey:
        if "label" in i and type(i["label"]) is list:
            survey_messages.append({"key_name": i["name"], "translation": i["label"][0]})

    for c in choices:
        if "label" in c and type(c["label"]) is list:
            survey_messages.append(
                {
                    "key_name": "{}.{}".format(c["list_name"], c["name"]),
                    "translation": c["label"][0],
                }
            )

    survey_keys = [k["key_name"] for k in survey_messages]

    for k in survey_messages:
        name = k["key_name"]
        translation = k["translation"]
        if not k["key_name"] in key_ids:

            print(f"kobo does not have key {name} will add: {translation}")
            keys_to_add.append(kobo_to_lokalise(k))
        else:
            lokalise_entry = [i for i in keys if i["key_name"]["web"] == k["key_name"]][0]
            lokalise_translation = [
                i["translation"]
                for i in lokalise_entry["translations"]
                if i["language_iso"] == "en"
            ][0]
            if lokalise_translation != translation:
                print(
                    f"kobo has key {name} will update from {lokalise_translation} to {translation}"
                )
                kobo_update = kobo_to_lokalise(k)
                kobo_update["key_id"] = list(
                    filter(lambda x: x["key_name"]["web"] == name, keys)
                )[0]["key_id"]
                keys_to_update.append(kobo_update)
            else:
                print(f"Kobo has key {name} and is up to date")
            # pprint(lokalise_translation)

    print("{} keys to add".format(len(keys_to_add)))
    print("{} keys to update".format(len(keys_to_update)))

    if len(keys_to_add) > 0:
        lokalise.keys_add(keys_to_add)
        print("added keys")

    if len(keys_to_update) > 0:
        pass
        pprint(keys_to_update)
