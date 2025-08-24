# LeetAI/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),

    # Chatbot app (namespaced)
    path("chatbot/", include(("chatbot.urls", "chatbot"), namespace="chatbot")),

    # Redirect root "/" to chatbot home by route name (safer than hardcoding URL)
    path("", RedirectView.as_view(pattern_name="chatbot:chatbot_home", permanent=False)),
]
