from django.contrib import admin
from .models import Cruise, CruiseType, CruiseCompany, CruiseCategory, CruiseSession, Booking, Brand

# ... (keep the existing admin classes for Cruise, CruiseType, CruiseCompany, CruiseSession, CruiseCategory, and Booking)

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'website', 'featured')
    list_filter = ('featured',)
    search_fields = ('name', 'description')
