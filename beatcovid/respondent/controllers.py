import logging
import uuid

from .models import Respondent, Session

logger = logging.getLogger(__name__)


def get_respondent_from_request(request):
    """
        Retrieves an existing respondent from the session

    """
    user_id = request.session.get("user", None)
    u = None

    if user_id:
        user_id = uuid.UUID(user_id)
        u = Respondent.objects.get(id=user_id)
        logger.debug(f"Retrieved user {u.id}")

    return u


def get_user_from_request(request):
    """
        Retrieves the user from the session

    """
    session_key = request.session._get_or_create_session_key()

    # backwards compat for v1.0
    if "uid" in request.COOKIES:
        session_key = request.COOKIES["uid"]
        s = Session.objects.filter(cookie_id=session_key).first()

        if s:
            return s.respondent

        logger.error(
            "Someone sent us an uid cookie but we don't have a session for them. It was {}".format(
                session_key
            )
        )

    u = get_respondent_from_request(request)
    s = None

    if not u:
        u = Respondent()
        u.save()
        request.session["user"] = str(u.id)
        logger.debug(f"Created new user {u.id}")

    if session_key:
        s = Session.objects.filter(cookie_id=session_key).first()

        if not s:
            s = Session()
            s.cookie_id = session_key
            s.respondent = u
            s.save()

    return s.respondent


def import_user_session(request, tracking_key):
    s = Session.objects.filter(cookie_id=tracking_key).first()

    if s:
        return str(s.respondent.id)

    u = Respondent()
    u.save()
    request.session["user"] = str(u.id)

    s = Session()
    s.cookie_id = tracking_key
    s.respondent = u
    s.save()

    return str(u.id)
