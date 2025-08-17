from django.urls import path

from . import views

urlpatterns = [
    path("", views.form_view, name="chatbot_home"),
    path("submit/", views.submit_chat, name="chatbot_submit"),
    path("ping/", views.ping, name="chatbot_ping"),
    path("diag/", views.diag, name="chatbot_diag"),   # <— add this
]
