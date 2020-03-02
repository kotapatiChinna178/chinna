import logging
from typing import Any, Dict, List

from django.utils import timezone
from rest_framework.request import Request
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages import (
    FileMessage, KeyboardMessage, PictureMessage, TextMessage, VideoMessage
)
from viberbot.api.viber_requests.viber_request import ViberRequest
from viberbot.api.viber_requests import (
    ViberMessageRequest, ViberConversationStartedRequest,
    ViberSubscribedRequest, ViberUnsubscribedRequest,
    ViberDeliveredRequest, ViberSeenRequest, ViberFailedRequest,
    create_request
)

from .base_messenger import BaseMessenger
from ..errors import MessengerException, NotSubscribed
from ..types import Message, MessageType


log = logging.getLogger(__name__)


class Viber(BaseMessenger):
    """
    IM connector for Viber REST API
    """

    def __init__(self, token: str, **kwargs):
        super().__init__(token, **kwargs)

        self.bot = Api(BotConfiguration(
            auth_token=token,
            name=kwargs.get('name'),
            avatar=kwargs.get('avatar'),
        ))

    def enable_webhook(self, url: str, **kwargs):
        return self.bot.set_webhook(url=url)

    def disable_webhook(self):
        return self.bot.unset_webhook()

    def get_account_info(self) -> Dict[str, Any]:
        # {
        #    "status":0,
        #    "status_message":"ok",
        #    "id":"pa:75346594275468546724",
        #    "name":"account name",
        #    "uri":"accountUri",
        #    "icon":"http://example.com",
        #    "background":"http://example.com",
        #    "category":"category",
        #    "subcategory":"sub category",
        #    "location":{
        #       "lon":0.1,
        #       "lat":0.2
        #    },
        #    "country":"UK",
        #    "webhook":"https://my.site.com",
        #    "event_types":[
        #       "delivered",
        #       "seen"
        #    ],
        #    "subscribers_count":35,
        #    "members":[
        #       {
        #          "id":"01234567890A=",
        #          "name":"my name",
        #          "avatar":"http://example.com",
        #          "role":"admin"
        #       }
        #    ]
        # }
        data = self.bot.get_account_info()
        account_info = {
            'id': data.get('id'),
            'username': data.get('name'),
            'info': data
        }
        return account_info

    def get_user_info(self, user_id: str, **kwargs) -> Dict[str, Any]:
        # {
        #    "status":0,
        #    "status_message":"ok",
        #    "message_token":4912661846655238145,
        #    "user":{
        #       "id":"01234567890A=",
        #       "name":"John McClane",
        #       "avatar":"http://avatar.example.com",
        #       "country":"UK",
        #       "language":"en",
        #       "primary_device_os":"android 7.1",
        #       "api_version":1,
        #       "viber_version":"6.5.0",
        #       "mcc":1,
        #       "mnc":1,
        #       "device_type":"iPhone9,4"
        #    }
        # }
        data = self.bot.get_user_details(user_id).get('user')
        user_info = {
            'id': data.get('id'),
            'username': data.get('name'),
            'info': {
                'avatar': data.get('avatar'),
                'country': data.get('country'),
                'language': data.get('language'),
                'primary_device_os': data.get('primary_device_os'),
                'api_version': data.get('api_version'),
                'viber_version': data.get('viber_version'),
                'device_type': data.get('device_type'),
            }
        }
        return user_info

    def parse_message(self, request: Request) -> Message:
        # NOTE: There is no way to get the body
        #       after processing the request in DRF.
        # # Verify signature
        # sign = request.META.get('HTTP_X_VIBER_CONTENT_SIGNATURE')
        # if not self.bot.verify_signature(request.body, sign):
        #     raise IMApiException(f'Viber message not verified; '
        #                          f'Data={request.data}; Sign={sign};')

        # Parse message data in to viber types
        vb_request = create_request(request.data)

        try:
            return self._get_message(vb_request)
        except Exception as err:
            # TODO: remove this after development
            log.exception(f'Parse message error; Message={vb_request}; '
                          f'Error={err};')
            return Message(MessageType.UNDEFINED)

    @staticmethod
    def _get_message(vb_request: ViberRequest) -> Message:
        if isinstance(vb_request, ViberMessageRequest):
            if isinstance(vb_request.message, TextMessage):
                return Message(
                    message_type=MessageType.TEXT,
                    message_id=vb_request.message_token,
                    user_id=vb_request.sender.id,
                    text=vb_request.message.text,
                    timestamp=vb_request.timestamp)
            elif isinstance(vb_request.message, PictureMessage):
                return Message(
                    message_type=MessageType.PICTURE,
                    message_id=vb_request.message_token,
                    user_id=vb_request.sender.id,
                    image_url=vb_request.message.media,
                    timestamp=vb_request.timestamp)
            elif isinstance(vb_request.message, VideoMessage):
                return Message(
                    message_type=MessageType.PICTURE,
                    message_id=vb_request.message_token,
                    user_id=vb_request.sender.id,
                    video_url=vb_request.message.media,
                    size=vb_request.message.size,
                    timestamp=vb_request.timestamp)
            else:
                return Message(
                    message_type=MessageType.TEXT,
                    message_id=vb_request.message_token,
                    user_id=vb_request.sender.id,
                    text=vb_request.message,
                    timestamp=vb_request.timestamp)
        elif isinstance(vb_request, ViberConversationStartedRequest):
            return Message(
                message_type=MessageType.START,
                message_id=vb_request.message_token,
                user_id=vb_request.user.id,
                user_name=vb_request.user.name,
                timestamp=vb_request.timestamp,
                context=vb_request.context)
        elif isinstance(vb_request, ViberSubscribedRequest):
            return Message(
                message_type=MessageType.SUBSCRIBED,
                user_id=vb_request.user.id,
                user_name=vb_request.user.name,
                timestamp=vb_request.timestamp)
        elif isinstance(vb_request, ViberUnsubscribedRequest):
            return Message(
                message_type=MessageType.UNSUBSCRIBED,
                user_id=vb_request.user_id,
                timestamp=vb_request.timestamp)
        elif isinstance(vb_request, ViberDeliveredRequest):
            return Message(
                message_type=MessageType.DELIVERED,
                message_id=vb_request.meesage_token,
                user_id=vb_request.user_id,
                timestamp=vb_request.timestamp)
        elif isinstance(vb_request, ViberSeenRequest):
            return Message(
                message_type=MessageType.SEEN,
                message_id=vb_request.meesage_token,
                user_id=vb_request.user_id,
                timestamp=vb_request.timestamp)
        elif isinstance(vb_request, ViberFailedRequest):
            log.warning(f'Client failed receiving message; Error={vb_request}')
            return Message(
                message_type=MessageType.FAILED,
                message_id=vb_request.meesage_token,
                user_id=vb_request.user_id,
                error=vb_request.desc)
        elif vb_request.event_type == 'webhook':
            return Message(
                message_type=MessageType.WEBHOOK,
                timestamp=vb_request.timestamp)
        else:
            log.warning(f'VRequest Type={type(vb_request)}; '
                        f'Object={vb_request};')
            return Message(
                message_type=MessageType.UNDEFINED,
                timestamp=vb_request.timestamp,
                event_type=vb_request.event_type)
            # raise IMApiException('Failed parse message; '
            #                      'Request object={}'.format(viber_request))

    def send_message(self, receiver: str, message: str,
                     button_list: list = None, **kwargs) -> str:
        kb = self._get_keyboard(button_list) if button_list else None

        if message:
            vb_message = TextMessage(text=message, keyboard=kb)
        else:
            vb_message = KeyboardMessage(keyboard=kb)

        try:
            return self.bot.send_messages(receiver, [vb_message])[0]
        except Exception as err:
            if str(err) == 'failed with status: 6, message: notSubscribed':
                raise NotSubscribed(err)
            raise MessengerException(err)

    def send_file(self, receiver: str, file_url: str,
                  file_size: int, file_name: str, file_type: str = None,
                  button_list: list = None, **kwargs) -> str:
        kb = self._get_keyboard(button_list) if button_list else None

        if file_type == 'image':
            message = PictureMessage(media=file_url, keyboard=kb)
        elif file_type == 'video':
            message = VideoMessage(media=file_url, size=file_size, keyboard=kb)
        else:
            message = FileMessage(media=file_url, size=file_size,
                                  file_name=file_name, keyboard=kb)

        try:
            return self.bot.send_messages(receiver, [message])[0]
        except Exception as err:
            if str(err) == 'failed with status: 6, message: notSubscribed':
                raise NotSubscribed(err)
            raise MessengerException(err)

    def welcome_message(self, text: str) -> Dict[str, str]:
        return {
            "sender": {
                "name": self.name,
                "avatar": self.avatar_url
            },
            "type": "text",
            "text": text
        }

    @staticmethod
    def _get_keyboard(buttons: list):
        if not buttons:
            return None

        kb = {
            'Type': 'keyboard',
            'BgColor': '#ffffff',
            'min_api_version': 6,
            'Buttons': []
        }

        for button in buttons:
            # if not isinstance(button, Button):
            #     continue

            _btn = {
                'Columns': 2,  # TODO: how is it storage in Model?
                'Rows': 1,
                'BgColor': '#aaaaaa',
                'ActionType': 'reply',
                'ActionBody': button.command,
                'Text': '<font color="{clr}"><b>{text}'
                        '</b></font>'.format(text=button.text, clr='#131313'),
                'TextVAlign': 'middle', 'TextHAlign': 'center',
                'TextOpacity': 60, 'TextSize': 'large',
                'TextPaddings': [12, 8, 8, 20],  # [up, left, right, bottom]
            }

            try:
                if hasattr(button, 'image'):
                    _btn.update(
                        BgMedia=f'https://bot.it-o.ru/static/img/{button.image}',
                        BgMediaScaleType='fill')
            except IndexError:
                pass

            kb['Buttons'].append(_btn)

        return kb
