# markets/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_view, name='main_view'),
    path('find-market-for-review/', views.find_market_for_review, name='find_market_for_review'),
    path('all/', views.view_all_markets, name='view_all_markets'), # Новая страница для всех рынков
    path('search/', views.search_markets, name='search_markets'),   # Страница результатов поиска
    path('market/<str:fmid>/', views.market_details, name='market_details'),
    path('market/<str:fmid>/review/', views.submit_review, name='submit_review'),
]