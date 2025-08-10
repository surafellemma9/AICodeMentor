from django.urls import path

from . import views

urlpatterns = [
    path("", views.form_view, name="chatbot_home"),         # GET form page
    path("submit/", views.submit_chat, name="chatbot_submit"),  # POST handler
    path("ping/", views.ping, name="chatbot_ping"),
]
