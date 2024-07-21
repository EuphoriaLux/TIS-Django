# cruises/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.cruise_list, name='cruise_list'),
    path('<int:cruise_id>/', views.cruise_detail, name='cruise_detail'),
    path('booking/<int:booking_id>/confirmation/', views.booking_confirmation, name='booking_confirmation'),
    path('book/<int:cruise_id>/', views.book_cruise, name='book_cruise'),
    
]