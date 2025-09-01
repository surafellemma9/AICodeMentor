# chatbot/urls.py
from django.urls import path
from . import views

app_name = "chatbot"

urlpatterns = [
    path("", views.chat_page, name="chatbot_home"),           # renders form.html and messages
    path("ask/", views.submit_chat, name="chatbot_ask"),      # <-- used by the forms in your template
    path("new/", views.new_chat, name="chatbot_new"),         # <-- used by the "+ New chat" link
    path("diag/", views.diag, name="diag"),
    path("ping/", views.ping, name="ping"),
]
