from django.urls import path

from .views import MessengerCallback, MessengerSwitch


app_name = 'bot_engine'

urlpatterns = [
    path('<int:id>/enable/', MessengerSwitch.as_view(),
         {'switch_on': True}, name='enable'),
    path('<int:id>/disable/', MessengerSwitch.as_view(),
         {'switch_on': False}, name='disable'),
    path('<str:hash>/', MessengerCallback.as_view(), name='webhook'),
]
