# quote/urls.py
from django.urls import path
from . import views

app_name = 'quote'

urlpatterns = [
    path('create-quote/<int:cruise_id>/', views.create_quote, name='create_quote'),
    #path('book-cruise/<int:cruise_id>/', views.book_cruise, name='book_cruise'),
    path('booking/confirmation/', views.booking_confirmation, name='quote_confirmation'),
    path('book-cruise-wizard/<int:cruise_id>/', views.CruiseBookingWizard.as_view(), name='book_cruise_wizard'),
    path('quote-confirmation/<int:quote_id>/', views.quote_confirmation, name='quote_confirmation'),
    
]