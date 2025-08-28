from django.urls import path
from . import views as cb

app_name = "chatbot"

urlpatterns = [
    path("", cb.chat_page, name="chatbot_home"),
    path("new/", cb.new_chat, name="chatbot_new"),
    path("ask/", cb.submit_chat, name="chatbot_ask"),   # ← this name must match the form action
]
