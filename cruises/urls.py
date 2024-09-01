# cruises/urls.py

from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


app_name = 'cruises'

urlpatterns = [
    path('', views.cruise_list, name='cruise_list'),
    path('<int:cruise_id>/', views.cruise_detail, name='cruise_detail'),
    path('river-cruises/', views.river_cruise_list, name='river_cruise_list'),
    path('maritime-cruises/', views.maritime_cruise_list, name='maritime_cruise_list'),
    path('cruise/<slug:cruise_slug>/flyer/', views.download_cruise_flyer, name='cruise_flyer'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)