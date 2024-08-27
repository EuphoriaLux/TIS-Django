# cruises/admin.py
from django.contrib import admin
from django.db.models import Sum
from django.utils import timezone
from .models import CruiseCompany, CruiseType, Brand, Cruise, CruiseCategory, CruiseCategoryPrice, CruiseSession, Equipment
from django.urls import reverse
from django.utils.html import format_html
from django.urls import path
from django.http import HttpResponse, FileResponse
from quote.utils import generate_quote_pdf
from django.shortcuts import get_object_or_404


class CruiseCategoryPriceInline(admin.TabularInline):
    model = CruiseCategoryPrice
    extra = 1

class CruiseSessionInline(admin.TabularInline):
    model = CruiseSession
    extra = 1

@admin.register(CruiseCompany)
class CruiseCompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'website')
    search_fields = ('name',)

@admin.register(CruiseType)
class CruiseTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'website', 'featured')
    list_filter = ('featured',)
    search_fields = ('name',)

@admin.register(Cruise)
class CruiseAdmin(admin.ModelAdmin):
    list_display = ('name', 'cruise_type', 'company', 'get_price_range', 'get_next_session', 'has_flyer', 'generate_flyer_button')
    list_filter = ('cruise_type', 'company')
    search_fields = ('name', 'description')
    inlines = [CruiseCategoryPriceInline, CruiseSessionInline]
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'cruise_type', 'company')
        }),
        ('Images', {
            'fields': ('image', 'image_url'),
            'classes': ('collapse',)
        }),
        ('Flyer', {
            'fields': ('flyer_pdf',),
            'classes': ('collapse',)
        }),
    )

    def get_price_range(self, obj):
        prices = CruiseCategoryPrice.objects.filter(cruise=obj)
        if prices.exists():
            min_price = prices.order_by('price').first().price
            max_price = prices.order_by('-price').first().price
            return f"€{min_price} - €{max_price}"
        return "N/A"
    get_price_range.short_description = "Price Range"

    def get_next_session(self, obj):
        next_session = CruiseSession.objects.filter(cruise=obj, start_date__gte=timezone.now()).order_by('start_date').first()
        return next_session.start_date if next_session else "No upcoming sessions"
    get_next_session.short_description = "Next Session"

    def has_flyer(self, obj):
        return bool(obj.flyer_pdf)
    has_flyer.boolean = True
    has_flyer.short_description = "Has Flyer"

    def generate_flyer_button(self, obj):
        url = reverse('admin:generate_flyer', args=[obj.pk])
        return format_html('<a class="button" href="{}">Generate Flyer</a>', url)
    generate_flyer_button.short_description = 'Generate Flyer'
    generate_flyer_button.allow_tags = True

    def generate_flyer_view(self, request, cruise_id):
        from .flyer.generator import CruiseFlyerGenerator  # Import here to avoid circular import
        generator = CruiseFlyerGenerator(cruise_id)
        flyer_path = generator.generate()
        return FileResponse(open(flyer_path, 'rb'), content_type='application/pdf')

        # Update the cruise object with the new flyer
        cruise = Cruise.objects.get(id=cruise_id)
        with open(flyer_path, 'rb') as f:
            cruise.flyer_pdf.save(f'cruise_flyer_{cruise_id}.pdf', f, save=True)
        
        return FileResponse(open(flyer_path, 'rb'), content_type='application/pdf')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('generate_flyer/<int:cruise_id>/', self.admin_site.admin_view(self.generate_flyer_view), name='generate_flyer'),
        ]
        return custom_urls + urls

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')

class EquipmentInline(admin.TabularInline):
    model = CruiseCategory.equipment.through
    extra = 1

@admin.register(CruiseCategory)
class CruiseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')
    filter_horizontal = ('equipment',)
    inlines = [EquipmentInline]

@admin.register(CruiseSession)
class CruiseSessionAdmin(admin.ModelAdmin):
    list_display = ('cruise', 'start_date', 'end_date', 'capacity', 'get_available_capacity')
    list_filter = ('cruise', 'start_date')
    search_fields = ('cruise__name',)

    def get_available_capacity(self, obj):
        booked = Booking.objects.filter(cruise_session=obj).aggregate(total=Sum('number_of_passengers'))['total'] or 0
        return obj.capacity - booked
    get_available_capacity.short_description = "Available Capacity"