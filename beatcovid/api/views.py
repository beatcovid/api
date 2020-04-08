import datetime
import logging
import re

from django.db.models import Avg, Count, F
from django.http import Http404
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

# valid KOBO form names
_clean_form_name = re.compile("[^a-zA-Z\-\_0-9]")


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def FormSubmission(request, form_id, submission):
    result = submit_form(form_id, submission)

    if not result:
        raise Http404

    return Response(result)


@api_view(["GET"])
def FormSchema(request, form_name):
    form_name = _clean_form_name.sub("", form_name)

    result = get_form_schema(form_name)

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
def FormData(request, form_id, query=None):
    form_name = _clean_form_name.sub("", form_name)

    result = get_submission_data(form_id, query)

    if not result:
        raise Http404

    return Response(result)
