from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from django.views.generic import RedirectView


def healthz(_request):  # returns 200 for Render health checks
    return HttpResponse("ok")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("chatbot/", include("chatbot.urls")),
    path("", RedirectView.as_view(url="/chatbot/", permanent=False)),
    path("healthz/", healthz),
]
