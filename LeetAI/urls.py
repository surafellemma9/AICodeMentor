# LeetAI/urls.py
from django.urls import path

from chatbot import views as cb

app_name = "chatbot"

urlpatterns = [
    path("chatbot/diag/", cb.diag, name="chatbot_diag"),
    path("chatbot/gemini_probe/", cb.gemini_probe, name="chatbot_gemini_probe"),

    # Main chat page (what your template renders)
    path("chatbot/", cb.chat_page, name="chatbot_home"),
    path("chatbot/new/", cb.new_chat, name="chatbot_new"),

    # AJAX/form endpoint
    path("chatbot/ask/", cb.submit_chat, name="chatbot_ask"),
]
