from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('chatbot.urls')),  # 👈 This connects your app’s URLs
]
