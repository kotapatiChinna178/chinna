import logging

from django import forms
from django.contrib import admin
from django.forms.widgets import Select
from django.template.defaultfilters import pluralize
from django.utils.translation import gettext_lazy as _

from .models import Messenger, Account, Menu, Button
from .types import Message, MessageType


log = logging.getLogger(__name__)


# class ChatbotSelectWidget(Select):
#     """
#     Widget that lets you choose between chatbot classes.
#     """
#     _choices = None
#
#     @staticmethod
#     def chatbots_as_choices():
#         if len(bot_handler.chatbots) <= 1:
#             # TODO scan apps
#             pass
#         tasks = list(sorted(name for name in bot_handler.chatbots))
#         return (('', ''), ) + tuple(zip(tasks, tasks))
#
#     @property
#     def choices(self):
#         if self._choices is None:
#             self._choices = self.chatbots_as_choices()
#         return self._choices
#
#     @choices.setter
#     def choices(self, _):
#         # ChoiceField.__init__ sets ``self.choices = choices``
#         # which would override ours.
#         pass
#
#
# class ChatbotChoiceField(forms.ChoiceField):
#     """
#     Field that lets you choose between chatbot classes.
#     """
#     widget = ChatbotSelectWidget
#
#     def valid_value(self, value):
#         return True
#
#
# class MessengerForm(forms.ModelForm):
#     """
#     Form that lets you create and modify periodic tasks.
#     """
#     handler = ChatbotChoiceField(
#         label=_('Chatbot handler'),
#         required=False, )
#
#     class Meta:
#         model = Messenger
#         exclude = ()
#
#     # def clean(self):
#     #     data = super().clean()
#     #     handler_class = data.get('handler_class')
#     #     return data


@admin.register(Messenger)
class MessengerAdmin(admin.ModelAdmin):
    # form = MessengerForm

    list_display = ('title', 'api_type', 'menu', 'proxy', 'is_active')
    list_filter = ('api_type', 'menu', 'is_active', 'updated')
    search_fields = ('title', 'api_type', 'token', 'hash')
    readonly_fields = ('is_active', 'hash')
    actions = ('enable_webhook', 'disable_webhook')
    fieldsets = (
        (None, {
            'fields': ('title', 'api_type', 'is_active', 'handler',
                       'welcome_text'),
            'classes': ('extrapretty', 'wide'),
        }),
        (_('Authenticate'), {
            'fields': ('token', ),
            'classes': ('extrapretty', 'wide'),
        }),
        (_('Proxy'), {
            'fields': ('proxy', ),
            'classes': ('extrapretty', 'wide'),
        })
    )

    class Meta:
        model = Messenger

    def enable_webhook(self, request, queryset):
        try:
            for messenger in queryset.all():
                messenger.enable_webhook()
            rows_updated = queryset.update(is_active=True)
            msg = _(f'{rows_updated} messenger{pluralize(rows_updated)} '
                    f'{pluralize(rows_updated, _("was,were"))} '
                    f'successfully enabled')
            self.message_user(request, msg)
        except Exception as err:
            log.exception(err)
    enable_webhook.short_description = _('Enable webhook selected messengers')

    def disable_webhook(self, request, queryset):
        for messenger in queryset.all():
            messenger.disable_webhook()
        rows_updated = queryset.update(is_active=False)
        msg = _(f'{rows_updated} messenger{pluralize(rows_updated)} '
                f'{pluralize(rows_updated, _("was,were"))} '
                f'successfully disabled')
        self.message_user(request, msg)
    disable_webhook.short_description = _('Disable webhook selected messengers')


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'messenger', 'menu', 'user',
                    'utm_source', 'is_active', 'updated')
    list_filter = ('messenger', 'utm_source', 'is_active', 'updated', 'created')
    search_fields = ('id', 'username', 'utm_source')
    readonly_fields = ('id', 'info', 'messenger',
                       'is_active', 'updated', 'created')
    actions = ('send_ping', )
    fieldsets = (
        (None, {
            'fields': ('id', 'is_active', 'username', 'user', 'messenger'),
            'classes': ('extrapretty', 'wide'),
        }),
        (_('Info'), {
            'fields': ('menu', 'context', 'utm_source', 'info',
                       'updated', 'created'),
            'classes': ('extrapretty', 'wide'),
        })
    )

    class Meta:
        model = Account

    def send_ping(self, request, queryset):
        # TODO: implement checking subscription
        queryset.all()[0].send_message(Message(message_type=MessageType.TEXT,
                                               text='ping'))
    send_ping.short_description = _('Check account')


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('title', 'message', 'comment', 'updated')
    list_filter = ('updated', 'created')
    search_fields = ('title', 'message', 'comment', 'handler')
    filter_horizontal = ('buttons', )
    fieldsets = (
        (None, {
            'fields': ('title', 'message', 'comment', 'handler', 'buttons'),
            'classes': ('extrapretty', 'wide'),
        }),
    )

    class Meta:
        model = Menu


# class ButtonSelectWidget(Select):
#     """
#     Widget that lets you choose between chatbot classes.
#     """
#     _choices = None
#
#     @staticmethod
#     def items_as_choices():
#         if len(bot_handler.chatbots) <= 1:
#             # TODO: scan apps
#             pass
#         tasks = list(sorted(name for name in bot_handler.menu_handlers))
#         return (('', ''), ) + tuple(zip(tasks, tasks))
#
#     @property
#     def choices(self):
#         if self._choices is None:
#             self._choices = self.items_as_choices()
#         return self._choices
#
#     @choices.setter
#     def choices(self, _):
#         # ChoiceField.__init__ sets ``self.choices = choices``
#         # which would override ours.
#         pass
#
#
# class ButtonChoiceField(forms.ChoiceField):
#     """
#     Field that lets you choose between chatbot classes.
#     """
#     widget = ButtonSelectWidget
#
#     def valid_value(self, value):
#         return True
#
#
# class ButtonForm(forms.ModelForm):
#     """
#     Form that lets you create and modify periodic tasks.
#     """
#     handler_method = ButtonChoiceField(
#         label=_('handler'),
#         required=False)
#
#     class Meta:
#         model = Button
#         exclude = ()


@admin.register(Button)
class ButtonAdmin(admin.ModelAdmin):
    # form = ButtonForm

    list_display = ('title', 'text', 'comment', 'next_menu',
                    'for_staff', 'for_admin', 'is_inline', 'is_active')
    list_filter = ('for_staff', 'for_admin', 'is_inline', 'is_active')
    search_fields = ('title', 'text', 'message', 'comment', 'command')
    readonly_fields = ('command', )
    fieldsets = (
        (None, {
            'fields': ('title', 'text', 'command',
                       'message', 'comment', 'handler', 'next_menu',
                       ('for_staff', 'for_admin'), ('is_inline', 'is_active')),
            'classes': ('extrapretty', 'wide'),
        }),
    )

    class Meta:
        model = Button
