from __future__ import annotations
import logging
from hashlib import md5
from typing import Any, Callable, List, Optional, Type
from uuid import uuid4

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.contrib.sites.models import Site
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.module_loading import import_string
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from rest_framework.request import Request

from .errors import MessengerException, NotSubscribed
from .messengers import BaseMessenger, MessengerType
from .types import Message, MessageType


__all__ = ('Account', 'Button', 'Menu', 'Messenger')

log = logging.getLogger(__name__)
BASE_HANDLER = 'bot_engine.bot_handlers.echo_handler'
BUTTON_HANDLER = 'bot_engine.bot_handlers.echo_handler'
ECHO_HANDLER = 'bot_engine.bot_handlers.echo_handler'


# class DynamicHandlerMixin:
#     """
#     This mixin allows you to call the function declared in
#     the "handler" field, and change the handler without restarting the server.
#     """
#     # prev_handler = models.CharField(
#     #     _('old handler'), max_length=256,
#     #     null=True, editable=False)
#
#     @property
#     def run_handler(self) -> Callable:
#         """
#         Call an object that implements the interface of the BaseBot class.
#         :return: handler object
#         """
#         # self.refresh_from_db(fields=['prev_handler', 'handler'])
#         #
#         # if self.prev_handler and self.prev_handler != self.handler:
#         #     # clean
#         #     del self._handler
#
#         if not hasattr(self, '_handler'):
#             # # update
#             # self.prev_handler = self.handler
#             # self.save()
#             # import
#             handler_class = import_string(self.handler)
#             self._handler = handler_class()
#
#         return self._handler


class Messenger(models.Model):
    title = models.CharField(
        _('title'), max_length=256,
        help_text=_('This name will be used as the sender name.'))
    api_type = models.CharField(
        _('API type'), max_length=256,
        choices=MessengerType.choices(),
        default=MessengerType.NONE.value)
    token = models.CharField(
        _('bot token'), max_length=256,
        default='', blank=True,
        help_text=_('Token or secret key.'))
    proxy = models.CharField(
        _('proxy'), max_length=256,
        default='', blank=True,
        help_text=_('Enter proxy uri with format '
                    '"schema://user:password@proxy_address:port"'))
    logo = models.CharField(
        _('logo'), max_length=256,
        default='', blank=True,
        help_text=_('Relative URL. Required for some messenger APIs: Viber.'))
    welcome_text = models.CharField(
        _('welcome text'), max_length=512,
        default='', blank=True,
        help_text=_('Welcome message. Will be sent in response to the opening'
                    ' of the dialog (not a subscribe event). May be used with'
                    ' some messaging programs: Viber.'))

    handler = models.CharField(
        _('main handler'), max_length=256,
        # choices=_handler_choices,
        default=ECHO_HANDLER,
        help_text=_('It processes all messages that do not fall into '
                    'the menu and button handlers. To implement a handler, '
                    f'implement a {BASE_HANDLER} interface.'))
    menu = models.ForeignKey(
        'Menu', models.SET_NULL,
        verbose_name=_('main menu'), related_name='messengers',
        null=True, blank=True,
        help_text=_('The root menu. For example, "Home".'))

    hash = models.CharField(
        _('token hash'), max_length=256,
        default='', editable=False)
    is_active = models.BooleanField(
        _('active'),
        default=False, editable=False,
        help_text=_('This flag changes when the webhook on the messenger API '
                    'server is activated/deactivated.'))
    updated = models.DateTimeField(
        _('updated'), auto_now=True)
    created = models.DateTimeField(
        _('created'), auto_now_add=True)

    class Meta:
        verbose_name = _('messenger')
        verbose_name_plural = _('messengers')
        unique_together = ('token', 'api_type')

    def __str__(self):
        return f'{self.title} ({self.api_type})'

    def __repr__(self):
        return f'<Messenger ({self.api_type}:{self.token[:10]})>'

    def get_webhook_enable_url(self):
        return reverse('bot_api:enable', kwargs={'id': self.id})

    def get_webhook_disable_url(self):
        return reverse('bot_api:disable', kwargs={'id': self.id})

    def token_hash(self) -> str:
        if not self.hash:
            self.hash = md5(self.token.encode()).hexdigest()
            self.save()
        return self.hash

    def dispatch(self, request: Request) -> Optional[Any]:
        """
        Entry point for current messenger account
        :param request: Rest framework request object
        :return: Answer data (optional)
        """
        message = self.api.parse_message(request)

        if message.user_id:
            account, created = (Account.objects.select_related('menu', 'user')
                                .get_or_create(id=message.user_id,
                                               defaults={'messenger': self,
                                                         'menu': self.menu, }))
            if created or not account.info:
                try:
                    user_info = self.api.get_user_info(message.user_id)
                    account.update(username=user_info.get('username'),
                                   info=user_info.get('info'),
                                   is_active=True)
                except MessengerException as err:
                    log.exception(err)
        else:
            account = None

        log.debug(f'\nMessage={message};\nAccount={account};')

        if message.is_service:
            if (message.type == MessageType.START and account
                    and self.welcome_text):
                return self.api.welcome_message(self.welcome_text)
            elif message.type == MessageType.UNSUBSCRIBED and account:
                account.update(is_active=False)
            # TODO: make service handler
            # self.process_service_message(message, account)
            return None

        message, account = self.api.preprocess_message(message, account)

        if account.menu:
            account.menu.process_message(message, account)
        else:
            self.process_message(message, account)

    def process_message(self, message: Message, account: Account):
        """
        Process the message with a bound handler.
        :param message: new incoming massage object
        :param account: message sender object
        :return: None
        """
        if self.handler:
            self.run_handler(message, account)

    @property
    def run_handler(self) -> Callable:
        if not hasattr(self, '_handler'):
            self._handler = import_string(self.handler)
        return self._handler

    def enable_webhook(self):
        domain = Site.objects.get_current().domain
        url = reverse('bot_api:webhook', kwargs={'hash': self.token_hash()})
        return self.api.enable_webhook(url=f'https://{domain}{url}')

    def disable_webhook(self):
        return self.api.disable_webhook()

    @property
    def api(self) -> BaseMessenger:
        if not hasattr(self, '_api'):
            domain = Site.objects.get_current().domain
            url = self.logo
            self._api = self._api_class(
                self.token, proxy=self.proxy, name=self.title,
                avatar=f'https://{domain}{url}'
            )
        return self._api

    @property
    def _api_class(self) -> Type[BaseMessenger]:
        """
        Returns the connector class of saved type.
        """
        return MessengerType(self.api_type).messenger_class


class AccountManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('user', 'messenger')


class Account(models.Model):
    id = models.CharField(
        _('account id'), max_length=256,
        primary_key=True)
    username = models.CharField(
        _('user name'), max_length=256,
        null=True, blank=True)
    utm_source = models.CharField(
        _('utm source'), max_length=256,
        null=True, blank=True)
    info = JSONField(
        _('information'),
        default=dict, blank=True)
    context = JSONField(
        _('context'),
        default=dict, blank=True)

    messenger = models.ForeignKey(
        'Messenger', models.SET_NULL,
        verbose_name=_('messenger'), related_name='accounts',
        null=True, blank=True)
    menu = models.ForeignKey(
        'Menu', models.SET_NULL,
        verbose_name=_('current menu'), related_name='accounts',
        null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, models.SET_NULL,
        verbose_name=_('user'), related_name='accounts',
        null=True, blank=True)

    is_active = models.BooleanField(
        _('active'),
        default=False, editable=False,
        help_text=_('This flag changes when the user account on '
                    'the messenger API server is subscribed/unsubscribed.'))
    updated = models.DateTimeField(
        _('last visit'), auto_now=True)
    created = models.DateTimeField(
        _('first visit'), auto_now_add=True)

    objects = AccountManager()

    class Meta:
        verbose_name = _('account')
        verbose_name_plural = _('accounts')
        unique_together = ('id', 'messenger')

    def __str__(self):
        return f'{self.username or self.id} ({self.messenger})'

    def __repr__(self):
        return f'<Account ({self.messenger}:{self.id})>'

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save()

    @property
    def avatar(self) -> str:
        return self.info.get('avatar') or ''

    def send_message(self, message: Message, buttons: List[Button] = None,
                     i_buttons: List[Button] = None):
        if self.menu:
            buttons = buttons or self.menu.buttons.filter(is_inline=False).all()
            i_buttons = (i_buttons or
                         self.menu.buttons.filter(is_inline=True).all())

        btn_list = buttons or None
        ibtn_list = i_buttons or None

        # TODO: make Massage parameter and handle him in api objects
        try:
            self.messenger.api.send_message(self.id, message.text,
                                            button_list=btn_list)
        except NotSubscribed:
            self.is_active = False
            log.warning(f'Account {self.username}:{self.id} is not subscribed.')
        except MessengerException as err:
            log.exception(err)


class Menu(models.Model):
    title = models.CharField(
        _('title'), max_length=256)
    message = models.CharField(
        _('message'), max_length=1024,
        null=True, blank=True,
        help_text=_('The text of the message sent when you get to this menu. '
                    'If empty, nothing is sent.'))
    comment = models.CharField(
        _('comment'), max_length=1024,
        null=True, blank=True,
        help_text=_('Comment text. Does not affect functionality.'))
    handler = models.CharField(
        _('handler'), max_length=256,
        default=ECHO_HANDLER, blank=True,
        help_text=_(f'Your handler implementation must implement '
                    f'the {BASE_HANDLER} interface.'))

    # TODO: implement button order
    buttons = models.ManyToManyField(
        'Button',
        verbose_name=_('buttons'), related_name='menus')

    updated = models.DateTimeField(
        _('updated'), auto_now=True)
    created = models.DateTimeField(
        _('created'), auto_now_add=True)

    class Meta:
        verbose_name = _('menu')
        verbose_name_plural = _('menus')
        unique_together = ('title', )

    def __str__(self):
        return self.title

    def __repr__(self):
        return f'<Menu ({self.title}:{self.id})>'

    def json_buttons(self) -> List[dict]:
        return [item.to_dict() for item in self.buttons.all()]

    def process_message(self, message: Message, account: Account):
        """
        Process the message with a bound handler.
        :param message: new incoming massage object
        :param account: message sender object
        :return: None
        """
        if message.is_button:
            buttons = self.buttons.filter(Q(command=message.text) |
                                          Q(text=message.text)).all()
            if len(buttons) == 0:
                buttons = Button.objects.filter(Q(command=message.text) |
                                                Q(text=message.text)).all()

            if buttons:
                buttons[0].process_button(message, account)

            if not buttons or len(buttons) > 1:
                log.warning('The number of buttons found is different from one.'
                            ' This can lead to unplanned behavior.'
                            ' We recommend making the buttons unique.')
        else:
            self.run_handler(message, account)

    @property
    def run_handler(self) -> Callable:
        if not hasattr(self, '_handler'):
            self._handler = import_string(self.handler)
        return self._handler


class Button(models.Model):
    title = models.CharField(
        _('title'), max_length=256)
    text = models.CharField(
        _('text'), max_length=256,
        help_text=_('Button text.'))
    message = models.CharField(
        _('message'), max_length=1024,
        null=True, blank=True,
        help_text=_('The text of the message sent during the processing of '
                    'a button click. If empty, nothing is sent.'))
    comment = models.CharField(
        _('comment'), max_length=1024,
        null=True, blank=True,
        help_text=_('Comment text. Does not affect functionality.'))

    handler = models.CharField(
        _('handler'), max_length=256,
        default=ECHO_HANDLER, blank=True,
        help_text=_(f'Your handler implementation must implement '
                    f'the {BUTTON_HANDLER} interface.'))
    next_menu = models.ForeignKey(
        'Menu', models.SET_NULL,
        verbose_name=_('next menu'), related_name='from_buttons',
        null=True, blank=True)
    for_staff = models.BooleanField(
        _('for staff users'),
        default=False, blank=True,
        help_text=_('Buttons with this flag are available only for user '
                    'accounts of site staff (django.contrib.auth).'))
    for_admin = models.BooleanField(
        _('for admin users'),
        default=False, blank=True,
        help_text=_('Buttons with this flag are available only for user '
                    'accounts of site admins (django.contrib.auth).'))

    command = models.CharField(
        _('command'), max_length=256,
        default='', editable=False)
    is_inline = models.BooleanField(
        _('inline'), default=False,
        help_text=_('Inline in message.'))
    is_active = models.BooleanField(
        _('active'), default=True)
    updated = models.DateTimeField(
        _('updated'), auto_now=True)
    created = models.DateTimeField(
        _('created'), auto_now_add=True)

    class Meta:
        verbose_name = _('button')
        verbose_name_plural = _('buttons')
        unique_together = ('command', )

    def __str__(self):
        return self.title

    def __repr__(self):
        return f'<Button ({self.title}:{self.command})>'

    def process_button(self, message: Message, account: Account):
        """
        Process the message with a bound handler.
        :param message: new incoming massage object
        :param account: message sender object
        :return: None
        """
        if self.message:
            account.send_message(Message.text(self.message))

        if self.next_menu:
            account.update(menu=self.next_menu)

            btn_list = self.next_menu.buttons.all() or None
            if self.next_menu.message:
                msg_text = self.next_menu.message
                account.send_message(Message.text(msg_text), buttons=btn_list)
            else:
                account.send_message(Message.keyboard(btn_list))

        if self.handler:
            self.run_handler(message, account)

    @property
    def run_handler(self) -> Callable:
        if not hasattr(self, '_handler'):
            self._handler = import_string(self.handler)
        return self._handler

    def save(self, *args, **kwargs):
        if not self.command:
            rnd = uuid4().hex[:6]
            self.command = slugify(f'btn-{self.title}-{rnd}')
        super().save(*args, **kwargs)

    @property
    def action(self) -> str:
        return self.handler or str(self.next_menu)

    def to_dict(self) -> dict:
        return {
            'text': self.title,
            'command': self.command,
            'size': (2, 1)
        }
