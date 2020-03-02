from django.apps import AppConfig


class BotEngineConfig(AppConfig):
    name = 'bot_engine'
    verbose_name = 'Django Bot Engine'

    # def ready(self):
    #     # ?
    #     BOT_API_CLIENT_MODEL = ''
    #     scan_apps_chatbots()
    # self.module.autodiscover('bot_handlers')
