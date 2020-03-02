from __future__ import annotations
from enum import Enum

from django.utils.translation import gettext_lazy as _


class MessageType(Enum):
    # Service types
    START = 'start'
    SUBSCRIBED = 'subscribed'
    UNSUBSCRIBED = 'unsubscribed'
    DELIVERED = 'delivered'
    SEEN = 'seen'
    WEBHOOK = 'webhook'
    FAILED = 'failed'
    UNDEFINED = 'undefined'
    # Common types
    TEXT = 'text'
    STICKER = 'sticker'
    PICTURE = 'picture'
    AUDIO = 'audio'
    VIDEO = 'video'
    FILE = 'file'
    CONTACT = 'contact'
    URL = 'url'
    LOCATION = 'location'
    RICHMEDIA = 'richmedia'
    BUTTON = 'button'
    KEYBOARD = 'keyboard'

    @classmethod
    def service_types(cls) -> tuple:
        return (
            cls.START, cls.SUBSCRIBED, cls.UNSUBSCRIBED,
            cls.DELIVERED, cls.SEEN, cls.WEBHOOK, cls.FAILED, cls.UNDEFINED,
        )

    @classmethod
    def common_types(cls) -> tuple:
        return (
            cls.TEXT, cls.STICKER, cls.PICTURE, cls.AUDIO, cls.VIDEO, cls.FILE,
            cls.CONTACT, cls.URL, cls.LOCATION, cls.RICHMEDIA, cls.KEYBOARD,
        )

    @classmethod
    def choices(cls) -> tuple:
        return tuple((x.value, _(x.value.capitalize())) for x in cls)


class Message:
    def __init__(self, message_type: MessageType,
                 message_id: str = None,
                 user_id: str = None,
                 timestamp: int = None,
                 text: str = None,
                 buttons: list = None,
                 **kwargs):
        self.type = message_type
        self.id = message_id
        self.user_id = user_id
        self.timestamp = timestamp
        self.text = text
        self.buttons = buttons

        # TODO: add messenger id and type. For what ?

        self.user_name = kwargs.get('user_name')
        self.context = kwargs.get('context')
        self.error = kwargs.get('error')

        self.kwargs = kwargs

    def __str__(self):
        return f'Message(token={self.id}, type={self.type}, account={self.user_id})'

    @property
    def is_common(self) -> bool:
        return self.type in MessageType.common_types()

    @property
    def is_service(self) -> bool:
        return self.type in MessageType.service_types()

    @property
    def is_text(self) -> bool:
        return self.type in [MessageType.TEXT, MessageType.URL]

    @property
    def is_button(self) -> bool:
        return self.type in [MessageType.BUTTON, MessageType.KEYBOARD]

    ##############################################
    # Class methods returning a new typed object #
    ##############################################

    @classmethod
    def text(cls, text: str):
        return cls(MessageType.TEXT, text=text)

    @classmethod
    def keyboard(cls, buttons: list):
        return cls(MessageType.KEYBOARD, buttons=buttons)
