# chatbot/urls.py
from django.urls import path

from . import views as cb

app_name = "chatbot"

urlpatterns = [
    # diagnostics
    path("diag/", cb.diag, name="chatbot_diag"),
    path("gemini_probe/", cb.gemini_probe, name="chatbot_gemini_probe"),

    # main chat UI
    path("", cb.chat_page, name="chatbot_home"),
    path("new/", cb.new_chat, name="chatbot_new"),

    # submit endpoint (AJAX or form)
    path("ask/", cb.submit_chat, name="chatbot_ask"),
]
