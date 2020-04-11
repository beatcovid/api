import datetime
import json
import logging
import re

from django.db.models import Avg, Count, F
from django.http import Http404, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .controllers import (
    get_form_schema,
    get_submission_data,
    get_submission_stats,
    submit_form,
)

logger = logging.getLogger(__name__)

# valid KOBO form names
_clean_form_name = re.compile("[^a-zA-Z\-\_0-9]")


@api_view(["POST"])
# @permission_classes([IsAuthenticated])
def FormSubmission(request, form_name):
    try:
        submission = json.loads(request.body)  # request.raw_post_data w/ Django < 1.4
    except KeyError:
        HttpResponseBadRequest("Malformed data")

    result = submit_form(form_name, submission)

    print(result)

    if not result:
        print("404")
        raise Http404

    return Response(result)


@api_view(["GET"])
def FormSchema(request, form_name):
    form_name = _clean_form_name.sub("", form_name)

    # @TODO avoid prop drilling request down
    result = get_form_schema(form_name, request)

    if not result:
        raise Http404

    return Response(result)


@api_view(["GET"])
def FormStats(request, form_name):
    form_name = _clean_form_name.sub("", form_name)

    result = get_submission_stats(form_name)

    if not result:
        raise Http404

    return Response(result)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def FormData(request, form_name, query=None):
    form_name = _clean_form_name.sub("", form_name)

    result = get_submission_data(form_name, query)

    if not result:
        raise Http404

    return Response(result)
