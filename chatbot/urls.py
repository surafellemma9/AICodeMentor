# chatbot/urls.py
from django.urls import path
from . import views

app_name = "chatbot"

urlpatterns = [
    path("", views.chat_page, name="chatbot_home"),
    path("submit/", views.submit_chat, name="submit_chat"),
    path("new/", views.new_chat, name="new_chat"),
    path("diag/", views.diag, name="diag"),
    path("ping/", views.ping, name="ping"),
    path("form/", views.form_view, name="form"),
]
