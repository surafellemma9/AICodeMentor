# chatbot/urls.py
from django.urls import path
from . import views

app_name = "chatbot"

urlpatterns = [
    path("", views.chat_page, name="chatbot_home"),
    path("c/<slug:convo_id>/", views.chat_page, name="chatbot_chat"),  # open a specific conversation
    path("ask/", views.submit_chat, name="chatbot_ask"),
    path("new/", views.new_chat, name="chatbot_new"),
    path("diag/", views.diag, name="diag"),
    path("ping/", views.ping, name="ping"),
]
