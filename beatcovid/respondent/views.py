import logging
import uuid

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Respondent, Session

logger = logging.getLogger(__name__)


def get_user(user_id, session_key):
    u = None
    s = None

    if user_id:
        user_id = uuid.UUID(hex=user_id)
        u = Respondent.objects.get(id=user_id)
        logger.debug(f"Retrieved user {u.id}")

    if not u:
        u = Respondent()
        u.save()
        logger.debug(f"Created new user {u.id}")

    if session_key:
        s = Session.objects.filter(cookie_id=session_key).first()

        if not s:
            s = Session()
            s.cookie_id = session_key
            s.respondent = u
            s.save()

    return s.respondent


@api_view(["GET"])
def UserDetailView(request):
    user = get_user(
        request.session.get("user", None), request.session._get_or_create_session_key()
    )

    request.session["user"] = user.id.hex

    # @TODO include this in the form response
    return Response({"user": str(user.id)})
