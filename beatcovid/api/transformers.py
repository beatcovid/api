import json


def parse_kobo_json(form_json):
    """
        Takes JSON form output from KOBO and translates it into
        something more useful we can use in our clients. preference
        is to do it here on the server to make it consistent for all
        client rather than messing about with managing the JSON on the
        client.

        @TODO write unit tests
    """
    _json = form_json
    choices = _json["content"]["choices"]
    survey = _json["content"]["survey"]
    # pprint(survey)

    _output = {
        "uid": _json["uid"],
        "name": _json["name"],
        "url": _json["url"],
        "date_created": _json["date_created"],
        "summary": _json["summary"],
        "date_modified": _json["date_modified"],
        "version_count": _json["version_count"],
        "has_deployment": _json["has_deployment"],
        "deployed_versions": _json["deployed_versions"],
        "translations": _json["content"]["translations"],
        "user": {},
    }

    steps = []
    step = {"questions": []}
    _globals = []
    _global = {}
    in_step = False
    q = {}
    for si in survey:
        if si["type"] == "begin_group":
            step = {"name": si["name"], "questions": []}
            if "label" in si:
                step["label"] = "".join(si["label"]).replace("\n", "")
            # q = {}
            in_step = True
        elif si["type"] == "end_group":
            steps.append(step)
            step = {"questions": []}
            in_step = False
        elif in_step:
            q = {"id": si["$kuid"], "name": si["name"], "type": si["type"]}

            if "label" in si:
                q["label"] = "".join(si["label"])

            if "appearance" in si:
                q["appearance"] = si["appearance"]

            if "relevant" in si:
                q["relevant"] = si["relevant"]

            if "hint" in si:
                q["hint"] = si["hint"]

            if "calculated" in si:
                q["value"] = si["calculated"]

            if "required" in si:
                q["required"] = si["required"]
            else:
                q["required"] = False

            if "constraint" in si:
                q["constraint"] = si["constraint"]

            if "constraint_message" in si:
                q["constraint_message"] = si["constraint_message"]

            if "select_from_list_name" in si:
                c = list(
                    filter(
                        lambda d: d["list_name"] == si["select_from_list_name"], choices
                    )
                )
                c = [
                    {
                        "id": si["name"],
                        "value": i["name"],
                        "label": "".join(i["label"]).replace("\n", ""),
                    }
                    for i in c
                ]
                q["choices"] = c

            step["questions"].append(q)
        else:
            _global = {
                "id": si["$kuid"],
                "name": si["name"],
                "type": si["type"],
            }

            # if si["type"] == "calculate":
            # _global["calculate"] = si["calculate"]

            _globals.append(_global)

    _output["survey"] = {"global": _globals, "steps": steps}
    return _output
