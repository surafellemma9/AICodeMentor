# LeetAI/urls.py
from django.urls import path, include

urlpatterns = [
    path("chatbot/", include(("chatbot.urls", "chatbot"), namespace="chatbot")),
]
