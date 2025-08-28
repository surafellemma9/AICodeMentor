from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("chatbot/", include(("chatbot.urls", "chatbot"), namespace="chatbot")),
    path("", RedirectView.as_view(pattern_name="chatbot:chatbot_home", permanent=False)),
]
