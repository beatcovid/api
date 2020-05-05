import html
import json
import logging
import re

import markdown
from django.utils.translation import get_language_from_request

logger = logging.getLogger(__name__)

__extract_iso_lang = re.compile("\(([a-z]{2})\)$")


def _strip_outer_tags(s):
    """ strips outer html tags """

    start = s.find(">") + 1
    end = len(s) - s[::-1].find("<") - 1

    return s[start:end]


def parse_form_label(labels, language_index=0):
    if not labels or len(labels) < 1:
        return ""

    if type(labels) is not list:
        labels = [labels]

    label = labels[language_index]

    if type(label) is list:
        label = "".join(label)

    if not label:
        return ""

    _output = label.replace("\n", "")

    _output = html.unescape(_output)

    _output = markdown.markdown(
        _output, extensions=["pymdownx.emoji", "pymdownx.smartsymbols", "extra"]
    )

    _output = _strip_outer_tags(_output)

    return _output


def _parse_question(si, choices, request, li):
    q = {"id": si["$kuid"]}

    mapped_fields = [
        "type",
        "name",
        "label",
        "appearance",
        "relevant",
        "hint",
        "calculated",
        "required",
        "constraint",
        "constraint_message",
        "calculation",
        "parameters",
    ]

    for f in mapped_fields:
        if f in si:
            q[f] = si[f]

    if "label" in q:
        q["label"] = parse_form_label(q["label"], li)

    if "required" not in q:
        q["required"] = False

    # load externs
    if "extern" in si and (si["extern"] == True or si["extern"].lower() == "true"):
        q["choices"] = load_externs(si["select_from_list_name"], request)

    # only load choices if it's not an extern
    elif "select_from_list_name" in si:
        c = list(filter(lambda d: d["list_name"] == si["select_from_list_name"], choices))
        c = [
            {
                "id": si["name"],
                "value": i["name"],
                "label": parse_form_label(i["label"], li),
            }
            for i in c
        ]
        q["choices"] = c

    return q


def language_from_locale(locale):
    if "-" in locale:
        language, country = locale.split("-")
    else:
        language = locale
        country = None
    return language, country


def load_externs(list_name, request):
    if list_name == "languages":
        from languages_plus.models import Language

        languages = []
        languages_top = []

        user_language = get_language_from_request(request)

        if not user_language:
            user_language = "en"

        for l in Language.objects.all():
            if l.iso_639_1 == user_language[:2]:
                languages_top.append(
                    {"id": "languages", "value": l.iso_639_1, "label": l.name_en}
                )
            else:
                languages.append(
                    {"id": "languages", "value": l.iso_639_1, "label": l.name_en}
                )

        languages_top.append({"id": "languages", "value": None, "label": "--"})

        return languages_top + languages


def extract_iso_from_language(language_str):
    m = __extract_iso_lang.search(language_str)
    if m:
        return m.group(1)

    return None


def get_language_index(languages, user_language, default_language="en"):
    if not type(languages) is list:
        languages = [languages]

    index = 0
    index_default = 0
    found_user_language = False
    language_isos = []

    for l in languages:
        schema_language_iso = extract_iso_from_language(l)
        if schema_language_iso == user_language:
            return index
        if schema_language_iso == default_language:
            index_default = index
        index += 1

    return index_default


def parse_kobo_json(form_json, request, user, last_submission=None):
    """
        Takes JSON form output from KOBO and translates it into
        something more useful we can use in our clients. preference
        is to do it here on the server to make it consistent for all
        client rather than messing about with managing the JSON on the
        client.

        @TODO write unit tests
    """
    if not user or not user.id:
        logger.error("did not receive a user id when transforming form")

    _json = form_json
    choices = _json["content"]["choices"]
    survey = _json["content"]["survey"]

    # language / translation support
    languages = _json["summary"]["languages"]
    language_default = _json["summary"]["default_translation"]
    language_default_code = extract_iso_from_language(language_default)

    user_language = get_language_from_request(request)
    li = get_language_index(languages, user_language, language_default_code)

    user_id = str(user.id)

    _output = {
        "uid": _json["uid"],
        "name": _json["name"],
        "url": _json["url"],
        "user": {
            "id": user_id,
            "language": user_language,
            # "country": user_locale,
            "submission": user.submissions,
            "last_login": user.last_login,
            "first_login": user.created_at,
        },
        "date_created": _json["date_created"],
        "summary": _json["summary"],
        "date_modified": _json["date_modified"],
        "version_count": _json["version_count"],
        "has_deployment": _json["has_deployment"],
        "deployed_versions": _json["deployed_versions"],
        "translations": _json["content"]["translations"],
    }

    retained = []

    steps = []
    step = {"questions": []}
    _globals = []
    _global = {}

    # @TODO translate here too
    _label_map = {k["name"]: k["label"][0] for k in choices}

    in_step = False
    q = {}
    for si in survey:
        if si["type"] == "begin_group" and not in_step:
            step = {"name": si["name"], "questions": []}
            if "label" in si:
                step["label"] = parse_form_label(si["label"], li)
            # q = {}
            in_step = True
        elif si["type"] == "end_group" and in_step:
            steps.append(step)
            in_step = False
        elif in_step:
            if "retain" in si:
                retained.append(si["name"])
            q = _parse_question(si, choices, request, li)

            if "name" in q and "label" in q:
                _label_map[q["name"]] = parse_form_label(q["label"], li)

            step["questions"].append(q)
        else:
            _global = _parse_question(si, choices, request, li)

            if _global["name"] == "user_id" and user_id:
                _global["calculation"] = user_id
                _global["required"] = True

            _globals.append(_global)

    # filter last submission
    if last_submission:
        _l = {k: last_submission[k] for k in retained if k in last_submission}
    else:
        _l = {}

    # attach if it contains values
    if len(list(_l.keys())):
        _output["user"]["last_submission"] = _l
    else:
        _output["user"]["last_submission"] = False

    _output["survey"] = {"global": _globals, "steps": steps}
    _output["labels"] = _label_map

    return _output
