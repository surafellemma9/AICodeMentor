from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="chatbot_home"),
    path("ping/", views.ping, name="chatbot_ping"),
    path("api/chat/", views.chat_api, name="chat_api"),  # keep if you have it
]
