from django.contrib import admin
from .models import Cruise, CruiseType, CruiseCompany, CruiseCategory, CruiseSession, Booking

class CruiseSessionInline(admin.TabularInline):
    model = CruiseSession
    extra = 1

class CruiseCategoryInline(admin.TabularInline):
    model = CruiseCategory
    extra = 1

@admin.register(Cruise)
class CruiseAdmin(admin.ModelAdmin):
    list_display = ('name', 'cruise_type', 'company', 'get_start_date', 'get_end_date', 'get_price_range', 'get_total_capacity')
    list_filter = ('cruise_type', 'company')
    search_fields = ('name', 'description')
    inlines = [CruiseSessionInline, CruiseCategoryInline]

    def get_start_date(self, obj):
        first_session = obj.sessions.order_by('start_date').first()
        return first_session.start_date if first_session else 'N/A'
    get_start_date.short_description = 'Start Date'

    def get_end_date(self, obj):
        last_session = obj.sessions.order_by('-end_date').first()
        return last_session.end_date if last_session else 'N/A'
    get_end_date.short_description = 'End Date'

    def get_price_range(self, obj):
        categories = obj.categories.all()
        if categories:
            min_price = min(category.price for category in categories)
            max_price = max(category.price for category in categories)
            return f'${min_price} - ${max_price}'
        return 'N/A'
    get_price_range.short_description = 'Price Range'

    def get_total_capacity(self, obj):
        return sum(session.capacity for session in obj.sessions.all())
    get_total_capacity.short_description = 'Total Capacity'

@admin.register(CruiseType)
class CruiseTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

@admin.register(CruiseCompany)
class CruiseCompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'website')

@admin.register(CruiseSession)
class CruiseSessionAdmin(admin.ModelAdmin):
    list_display = ('cruise', 'start_date', 'end_date', 'capacity')
    list_filter = ('cruise', 'start_date')

@admin.register(CruiseCategory)
class CruiseCategoryAdmin(admin.ModelAdmin):
    list_display = ('cruise', 'name', 'price')
    list_filter = ('cruise',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'cruise_session', 'cruise_category', 'booking_date', 'status')
    list_filter = ('status', 'cruise_session__cruise', 'cruise_category')
    search_fields = ('first_name', 'last_name', 'email')