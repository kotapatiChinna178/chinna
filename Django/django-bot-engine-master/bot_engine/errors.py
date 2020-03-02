
class BotApiError(Exception):
    """
    Bot API exception class
    """


class MessengerException(BotApiError):
    """
    Instant Messenger exception class
    """


class NotSubscribed(BotApiError):
    """
    Account not subscribed
    """
