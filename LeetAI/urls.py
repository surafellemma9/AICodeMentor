from django.http import HttpResponse


def healthz(_): return HttpResponse("ok")

urlpatterns = [
    path("chatbot/", include("chatbot.urls")),
    path("", RedirectView.as_view(url="/chatbot/", permanent=False)),
    path("healthz/", healthz),
]
