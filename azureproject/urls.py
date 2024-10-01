from django.contrib import admin
from django.urls import path, include
from cruises.views import home,about,contact,FeaturedCruisesView  # Import the home view
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin/', include('nested_admin.urls')),
    path('', home, name='home'),  # Add this line for the home page
    path('cruises/', include('cruises.urls')),  # Make sure this line is present
    path('about/', about, name='about'),
    path('contact/', contact, name='contact'),
    path('featured-cruises/', FeaturedCruisesView.as_view(), name='featured_cruises'),
    path('quote/', include('quote.urls')),  # Update this line
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)