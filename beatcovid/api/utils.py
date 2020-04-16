from ua_parser import user_agent_parser


def get_user_agent(request):
    ua = request.META["HTTP_USER_AGENT"]

    if not ua:
        return None

    ua_parsed = user_agent_parser.Parse(ua)

    ret = {"useragent": ua}

    if "device" in ua_parsed:
        ret["device"] = ua_parsed["device"]

    if "os" in ua_parsed:
        ret["os"] = ua_parsed["os"]

    return ret
