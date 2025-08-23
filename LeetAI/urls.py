from django.urls import path, include

urlpatterns = [
    path("chatbot/", include(("chatbot.urls", "chatbot"), namespace="chatbot")),
    # Optional: make site root land on chat
    # from django.views.generic import RedirectView
    # path("", RedirectView.as_view(pattern_name="chatbot:chatbot_home", permanent=False)),
]
