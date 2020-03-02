from enum import Enum
from typing import Optional, Type

from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from .base_messenger import BaseMessenger
from .telegram import Telegram
from .viber import Viber


__all__ = (
    'MessengerType', 'BaseMessenger',
    'Telegram', 'Viber',
)


class MessengerType(Enum):
    NONE = 'none'
    # MESSENGER = 'messenger'
    # SKYPE = 'skype'
    # SLACK = 'slack'
    TELEGRAM = 'telegram'
    VIBER = 'viber'
    # WECHAT = 'wechat'
    # WHATSAPP = 'whatsapp'

    # TODO: implement __new__() with auto-adding fields

    @classmethod
    def choices(cls) -> tuple:
        return tuple((x.value, _(x.value.capitalize())) for x in cls)

    @property
    def messenger_classes(self) -> dict:
        return {m_type: f'bot_api.messengers.{m_type.value.capitalize()}'
                for m_type in self.__class__}

    @property
    def messenger_class(self) -> Optional[Type[BaseMessenger]]:
        if self == MessengerType.NONE:
            return None
        return import_string(f'bot_api.messengers.{self.value.capitalize()}')
