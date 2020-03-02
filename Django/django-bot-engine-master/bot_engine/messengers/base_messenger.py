from typing import Any, Dict, List, Optional, Tuple

from rest_framework.request import Request

from ..types import Message


class BaseMessenger:
    """
    Base class for IM connector
    """

    def __init__(self, token: str, **kwargs):
        self.token = token
        self.proxy_addr = self._proxy(kwargs.get('proxy'))
        self.name = kwargs.get('name')
        self.avatar_url = kwargs.get('avatar')

    def enable_webhook(self, url: str, **kwargs):
        """
        Initialize API IM webhook
        """
        raise NotImplementedError('`enable_webhook()` must be implemented.')

    def disable_webhook(self):
        """
        Uninitialize API IM webhook
        """
        raise NotImplementedError('`disable_webhook()` must be implemented.')

    def get_account_info(self) -> Dict[str, Any]:
        """
        Account info from IM service
        """
        raise NotImplementedError('`get_account_info()` must be implemented.')

    def get_user_info(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """
        User info from IM service
        """
        raise NotImplementedError('`get_user_info()` must be implemented.')

    def parse_message(self, request: Request) -> Message:
        """
        Parse incoming message
        """
        raise NotImplementedError('`_parse_message()` must be implemented.')

    def preprocess_message(self, message, account) -> tuple:
        """
        Preprocess message data
        Need for Telegram API for check - message is button?
        """
        return message, account

    def send_message(self, receiver: str, message: Message,
                     button_list: list = None,
                     inline_button_list: list = None, **kwargs) -> str:
        """
        Send message method
        """
        raise NotImplementedError('`send_message()` must be implemented.')

    def welcome_message(self, text: str) -> Dict[str, str]:
        """
        Return welcome message object method
        """
        raise NotImplementedError('`welcome_message()` must be implemented.')

    @staticmethod
    def _proxy(proxy_url: Optional[str]) -> Optional[Dict[str, str]]:
        if proxy_url:
            return {'https': proxy_url, 'http': proxy_url}
        return None
