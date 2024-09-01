# quote/urls.py
from django.urls import path
from . import views

app_name = 'quote'

urlpatterns = [
    path('create-quote/<int:cruise_id>/', views.create_quote, name='create_quote'),
    path('quote-cruise/<int:cruise_id>/', views.quote_cruise, name='quote_cruise'),
    path('quote-confirmation/', views.quote_confirmation, name='quote_confirmation'),
    
]
