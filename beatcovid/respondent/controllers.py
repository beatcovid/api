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
    v1_session_key = None
    device_id = None

    # backwards compat for v1.0
    if "uid" in request.COOKIES:
        v1_session_key = request.COOKIES["uid"]

    if v1_session_key:
        s = Session.objects.filter(cookie_id=v1_session_key).first()

        if s:
            return s.respondent

        logger.error(
            "Someone sent us an uid cookie but we don't have a session for them. It was {}".format(
                v1_session_key
            )
        )

    if "HTTP_X_UID" in request.META:
        logger.debug(
            "Getting uid from request header {}".format(request.META["HTTP_X_UID"])
        )
        device_id = request.META["HTTP_X_UID"]

    if device_id:
        s = Session.objects.filter(device_id=device_id).first()

        if s:
            return s.respondent

        u = Respondent()
        u.save()
        request.session["user"] = str(u.id)
        logger.debug(f"Created new user from device id {u.id}")
        s = Session()
        s.device_id = device_id
        s.respondent = u
        s.save()

        return u

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
