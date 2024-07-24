# cruises/urls.py

from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.cruise_list, name='cruise_list'),
    path('<int:cruise_id>/', views.cruise_detail, name='cruise_detail'),
    path('booking/<int:booking_id>/confirmation/', views.booking_confirmation, name='booking_confirmation'),
    path('book/<int:cruise_id>/', views.book_cruise, name='book_cruise'),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)