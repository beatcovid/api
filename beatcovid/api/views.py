import datetime
import json
import logging
import re
import uuid

from django.db.models import Avg, Count, F
from django.http import Http404, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.utils.translation import get_language_from_request
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_page
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from beatcovid.respondent.controllers import get_user_from_request

from .controllers import (
    get_form_schema,
    get_stats,
    get_submission_data,
    get_submission_stats,
    get_user_submissions,
    submit_form,
)

logger = logging.getLogger(__name__)

# valid KOBO form names
_clean_form_name = re.compile("[^a-zA-Z\-\_0-9]")


@api_view(["POST"])
def FormSubmission(request, form_name):
    user = get_user_from_request(request)

    submission = request.data

    if "user_id" in submission:
        submitted_user = submission["user_id"]
        if submitted_user != str(user.id):
            logger.info(
                f"Mismatch error: User is {user.id} while submitted is {submitted_user} "
            )
            # raise HttpResponseBadRequest("User mismatch")

    result = submit_form(form_name, submission, user, request)

    if not result:
        raise Http404

    return Response(result)


@api_view(["GET"])
def FormSchema(request, form_name):
    user = get_user_from_request(request)
    form_name = _clean_form_name.sub("", form_name)

    # @TODO avoid prop drilling request down
    result = get_form_schema(form_name, request, user)

    if not result:
        raise Http404

    return Response(result)


@api_view(["GET"])
def FormStats(request, form_name):
    form_name = _clean_form_name.sub("", form_name)

    result = get_stats(form_name)

    if not result:
        raise Http404

    r = Response(result)
    r["access-control-allow-credentials"] = "true"

    return r


@api_view(["GET"])
def UserSubmissionView(request, form_name="beatcovid19now"):
    form_name = _clean_form_name.sub("", form_name)
    user = get_user_from_request(request)

    if not user:
        raise Http404

    result = get_user_submissions(form_name, user)

    return Response(result)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def FormData(request, form_name):
    form_name = _clean_form_name.sub("", form_name)
    query = request.GET.get("query", None)
    count = request.GET.get("count", None)
    sort = request.GET.get("sort", None)

    query = json.loads(query)

    _q = {
        "query": query,
    }

    if count:
        _q["limit"] = count

    if sort:
        _q["sort"] = sort

    result = get_submission_data(form_name, _q)

    if not result:
        raise Http404

    return Response(result)


@api_view(["GET"])
def TranslationTest(request):
    result = {
        "test": _("condition.immune_system"),
        "lang": request.LANGUAGE_CODE,
    }
    return Response(result)
