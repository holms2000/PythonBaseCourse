# task11/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('users/', include('users.urls')), # Все URL пользователей будут начинаться с /users/
    path('', include('markets.urls')),
]