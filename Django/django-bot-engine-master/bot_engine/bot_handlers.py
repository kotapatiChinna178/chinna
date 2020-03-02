from .models import Account
from .types import Message


__all__ = ('echo_handler', )


def echo_handler(message: Message, account: Account):
    """
    Simple echo chat bot.
    """
    account.send_message(message)
