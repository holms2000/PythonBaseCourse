from django.urls import path
from .views import api_router

urlpatterns = [
    path('api/', api_router),
]