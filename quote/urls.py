# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('create-quote/', views.create_quote, name='create_quote'),
    # Add more URL patterns
]