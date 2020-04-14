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

    def create_transition_instance(self, respondent):
        key = ''
        while True:
            key = self.generate_short_key()
            exists = TransitionAssistant.objects.filter(transfer_key=key).count()
            if exists == 0:
                break
        TransitionAssistant(respondent=respondent, transfer_key = key).save()
        return key

    def get(self, request, format=None):
        # @TODO get the user somehow, not sure how to use the API view:
        respondent = Respondent.objects.first()

        key = self.create_transition_instance(respondent)
        return Response([key])


class GetUID(APIView):
    def get(self, request, format=None):
        from datetime import datetime
        # @TODO get the key from the request:
        key= "ABC123"

        now = datetime.now()
        transtion = TransitionAssistant.objects().get(key=key)
        value = "unknown"
        if transition.count() == 1:
            if now > respondent.first()["expires_at"]:
                value = "expired"
            else:
                value = respondent.first()["uid"]

        return Response([value])
