from django.contrib import admin
from .models import Cruise, CruiseType, CruiseCompany, CruiseCategory, CruiseSession, Booking, Brand

@admin.register(CruiseCompany)
class CruiseCompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'website')
    search_fields = ('name', 'description')

@admin.register(CruiseType)
class CruiseTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'website', 'featured')
    list_filter = ('featured',)
    search_fields = ('name', 'description')

class CruiseCategoryInline(admin.TabularInline):
    model = CruiseCategory
    extra = 1

class CruiseSessionInline(admin.TabularInline):
    model = CruiseSession
    extra = 1

@admin.register(Cruise)
class CruiseAdmin(admin.ModelAdmin):
    list_display = ('name', 'cruise_type', 'company')
    list_filter = ('cruise_type', 'company')
    search_fields = ('name', 'description')
    inlines = [CruiseCategoryInline, CruiseSessionInline]

@admin.register(CruiseCategory)
class CruiseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'cruise', 'price')
    list_filter = ('cruise',)
    search_fields = ('name', 'description')

@admin.register(CruiseSession)
class CruiseSessionAdmin(admin.ModelAdmin):
    list_display = ('cruise', 'start_date', 'end_date', 'capacity')
    list_filter = ('cruise', 'start_date')
    search_fields = ('cruise__name',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'cruise_session', 'cruise_category', 'first_name', 'last_name', 'booking_date', 'status')
    list_filter = ('status', 'booking_date', 'cruise_session__cruise')
    search_fields = ('first_name', 'last_name', 'email')
    readonly_fields = ('booking_date', 'total_price')
