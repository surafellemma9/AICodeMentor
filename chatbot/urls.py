from django.urls import path

from . import views

app_name = "chatbot"

urlpatterns = [
    path("", views.chat_page, name="chat"),         # ChatGPT-style page
    path("ask/", views.submit_chat, name="ask"),    # POST endpoint (form or AJAX)
    path("form/", views.form_view, name="form"),    # optional legacy
    path("ping/", views.ping, name="ping"),
    path("diag/", views.diag, name="diag"),
]
