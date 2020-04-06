import datetime
import logging
import re

from django.db.models import Avg, Count, F
from django.http import Http404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .controllers import get_form_schema

# valid KOBO form names
_clean_form_name = re.compile("[^a-zA-Z\-\_0-9]")


@api_view(["GET"])
def FormSchema(request, form_name):
    # form_name = request.GET.get("form_name", "").strip()

    form_name = _clean_form_name.sub("", form_name)

    result = get_form_schema(form_name)

    if not result:
        raise Http404

    return Response(result)
