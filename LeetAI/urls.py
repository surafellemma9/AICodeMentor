# LeetAI/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),

    # Chatbot app routes
    path("chatbot/", include("chatbot.urls")),

    # Redirect the root URL ("/") to the chatbot home
    path("", RedirectView.as_view(url="/chatbot/", permanent=False)),
]
