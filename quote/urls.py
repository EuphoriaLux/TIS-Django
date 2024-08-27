# quote/urls.py
from . import views
from django.urls import path

app_name = 'quote'

urlpatterns = [
    path('create-quote/<int:cruise_id>/', views.create_quote, name='create_quote'),

    path('book-cruise/<int:cruise_id>/', views.book_cruise, name='book_cruise'),

    path('booking/<int:booking_id>/confirmation/', views.booking_confirmation, name='booking_confirmation'),

]