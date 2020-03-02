import logging

# from .chatbots import EchoBot


__title__ = 'Django bot api'
__version__ = '0.1.0'
__author__ = 'Aleksey Terentyev'
__license__ = 'Apache 2.0'
__copyright__ = 'Copyright 2019-2020 Aleksey Terentyev'

log = logging.getLogger(__name__)


class HandlersStorage:
    """

    """
    _chatbot_classes = {}
    _menu_items = {}

    # def __init__(self):
    #     self._chatbot_classes['bot_engine.chatbots:EchoBot'] = EchoBot

    def chatbot(self, cls):
        wrapped_class = '%s:%s' % (cls.__module__, cls.__name__)
        self._chatbot_classes[wrapped_class] = cls

        log.debug('wrapped_class={};'.format(wrapped_class))
        # class Wrapper(cls):
        #     print(cls.__module__, cls.__name__)
        #     return cls(*args, **kwargs)
        return cls

    def menu_item(self, func):
        wrapped_function = '%s:%s' % (func.__module__, func.__name__)
        self._menu_items[wrapped_function] = func

        # @wraps(func)
        # def wrapper(*args, **kwargs):
        #     print(func.__module__, func.__name__)
        #     return func(*args, **kwargs)
        return func

    @property
    def chatbots(self):
        return self._chatbot_classes

    @property
    def menu_handlers(self):
        return self._menu_items


bot_handler = HandlersStorage()
