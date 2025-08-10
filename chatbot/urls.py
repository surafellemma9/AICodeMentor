from django.urls import path

from . import views

urlpatterns = [
    path("", views.form_view, name="chatbot_home"),
    path("submit/", views.submit_chat, name="chatbot_submit"),
    path("ping/", views.ping, name="chatbot_ping"),  # keep for quick checks
]
