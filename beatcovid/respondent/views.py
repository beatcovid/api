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


class TransferRequest(APIView):

    def generate_short_key(self, length=6):
        from random import choice
        from string import ascii_letters, digits
        char_set = ascii_letters + digits
        key = ''.join(choice(char_set) for i in range(length))
        return key

    def get_or_create_transition_instance(self, respondent):
        ta = TransitionAssistant.objects.filter(respondent=respondent)
        ta_exists = ta.count()
        if ta_exists:
            key = ta.first().key
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
        from datetime import datetime
        from pytz import utc

        value = "transfer_key not provided"
        key = request.POST.get("transfer_key")

        if key:
            now = datetime.now()
            # @TODO verify we store UTC
            now = utc.localize(now)
            transition = TransitionAssistant.objects.filter(transfer_key=key)
            value = "unknown"
            if transition.count() == 1:
                if now > transition.first().expires_at:
                    value = "expired"
                else:
                    value = transition.first().respondent.id

        return Response({"id": str(value)})
