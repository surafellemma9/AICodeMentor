# chatbot/urls.py
from django.urls import path

from . import views

app_name = "chatbot"

urlpatterns = [
    path("", views.form_view, name="chatbot_home"),
    path("ask/", views.submit_chat, name="ask"),
]
