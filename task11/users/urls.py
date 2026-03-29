# users/urls.py

from django.urls import path
from .views import login_view, logout_view, profile_view # register_view здесь больше нет

urlpatterns = [
    path('login/', login_view, name='login'),
    # path('register/', register_view, name='register'), # <-- УДАЛИТЕ ЭТУ СТРОКУ
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
]