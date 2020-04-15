import datetime
import json
import logging
import re
import uuid

from django.http import Http404, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from beatcovid.respondent.controllers import get_user_from_request

from .controllers import get_user_report


@api_view(["GET"])
def SymptomTracker(request):
    user = get_user_from_request(request)

    if not user:
        raise Http404

    result = get_user_report(user)

    if not result:
        raise Http404

    r = Response(result)
    r["access-control-allow-credentials"] = "true"

    return r
