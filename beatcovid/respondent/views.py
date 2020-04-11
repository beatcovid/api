import logging

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .controllers import get_user_from_request

logger = logging.getLogger(__name__)


@api_view(["GET"])
def UserDetailView(request):
    user = get_user_from_request(request)

    # @TODO include this in the form response
    return Response({"user": str(user.id)})
