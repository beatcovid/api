import logging

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .controllers import get_user_from_request
from .models import Respondent, TransitionAssistant

logger = logging.getLogger(__name__)


@api_view(["GET"])
def UserDetailView(request):
    user = get_user_from_request(request)

    # @TODO include this in the form response
    return Response({"user": str(user.id)})


def check_if_expired(expiry_date, minimum_minutes=0):
    """
       Check if the time now + minimum_minutes is after the expiry date
    """
    from datetime import datetime, timedelta
    from pytz import utc

    now = datetime.now() + timedelta(minutes=minimum_minutes)
    # @TODO verify we store UTC
    now = utc.localize(now)
    if now > expiry_date:
        return True
    else:
        return False

class TransferRequest(APIView):
    """
    Get an existing transfer key if valid for at least MIN_VALID minutes
    or generate a new one.
    """
    MIN_VALID=5
    def generate_short_key(self, length=6):
        from random import choice
        from string import ascii_letters, digits
        char_set = ascii_letters + digits
        key = ''.join(choice(char_set) for i in range(length))
        return key

    def get_or_create_transition_instance(self, respondent):
        ta = TransitionAssistant.objects.filter(respondent=respondent).order_by("-expires_at")
        ta_exists = ta.count()
        if ta_exists and not check_if_expired(ta.first().expires_at,
                                              minimum_minutes=MIN_VALID):
                key = ta.first().transfer_key
        else:
            key = ''
            while True:
                key = self.generate_short_key()
                exists = TransitionAssistant.objects.filter(transfer_key=key).count()
                if exists == 0:
                    break
            TransitionAssistant(respondent=respondent, transfer_key = key).save()
        return key

    def get(self, request, format=None):
        respondent = get_user_from_request(self.request)

        key = self.get_or_create_transition_instance(respondent)
        return Response({"transfer_key": str(key)})


class GetUID(APIView):
    def get(self, request):
        value = "transfer_key not provided"
        key = request.POST.get("transfer_key")
        if key:
            ta = TransitionAssistant.objects.filter(transfer_key=key).order_by("-expires_at")
            value = "unknown"
            if ta.count() == 1:
                if check_if_expired(ta.first().expires_at):
                    value = "expired"
                else:
                    value = ta.first().respondent.id

        return Response({"id": str(value)})
