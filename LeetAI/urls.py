from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from django.views.generic import RedirectView


def healthz(_): return HttpResponse("ok")
def ping(_): return HttpResponse("pong")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("chatbot/", include("chatbot.urls")),      # all chatbot routes
    path("healthz/", healthz),                      # for Render health checks
    path("ping/", ping),                            # quick sanity check
    path("", RedirectView.as_view(url="/chatbot/", permanent=False)),  # / -> /chatbot/
]
