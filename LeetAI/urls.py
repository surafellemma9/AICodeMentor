from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("chatbot/", include(("chatbot.urls", "chatbot"), namespace="chatbot")),
    # Optional: make chatbot the homepage
    path("", RedirectView.as_view(pattern_name="chatbot:chatbot_home", permanent=False)),
]

# (optional) static files in DEBUG
from django.conf import settings
from django.conf.urls.static import static
if getattr(settings, "DEBUG", False):
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
