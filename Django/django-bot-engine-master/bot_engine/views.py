import logging

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import permissions
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView

from .models import Messenger


log = logging.getLogger(__name__)


class MessengerSwitch(APIView):
    """
    View for activate and deactivate webhooks
    """
    @staticmethod
    def post(request: Request, **kwargs) -> Response:
        switch_on = kwargs.get('switch_on')
        messenger_id = kwargs.get('id')
        try:
            messenger = Messenger.objects.get(id=messenger_id)
        except Messenger.DoesNotExist as err:
            log.exception(err)
            raise NotFound('Handler not found.')

        if switch_on:
            messenger.enable_webhook()
        else:
            messenger.disable_webhook()

        return Response()


@method_decorator(csrf_exempt, name='dispatch')
class MessengerCallback(APIView):
    """
    Messengers callbacks
    """
    permission_classes = (permissions.AllowAny, )

    # @classmethod
    # def as_view(cls, **initkwargs):
    #     """
    #     This method is overridden to avoid a rare error
    #     when not deactivating CSRF protection.
    #     """
    #     view = super().as_view(**initkwargs)
    #     view.csrf_exempt = True
    #     return view

    @staticmethod
    def post(request: Request, **kwargs) -> Response:
        log.debug(f'Bot Api POST; Message={request.data};')
        im_hash = kwargs.get('hash', '')

        try:
            messenger = Messenger.objects.get(hash=im_hash)
            answer = messenger.dispatch(request)
        except Messenger.DoesNotExist as err:
            log.exception(f'Messenger not found; Hash={hash}; Error={err};')
            raise NotFound('Handler not found.')

        log.debug(f'Bot Api POST; Answer={answer};')
        return Response(answer)
