from django import forms
from django.contrib import admin
from django.db import transaction
from django.db.models import Min, Max
from django.utils import timezone
from django.utils.formats import localize
from django.urls import reverse, path
from django.utils.html import format_html
from django.http import HttpResponse
from django.contrib import messages
from django.shortcuts import redirect
from .models import (
    CruiseCompany, CruiseType, Brand, Cruise, CruiseSession, Equipment,
    CabinType, CruiseCabinPrice, CruiseItinerary, Port, Excursion, CabinTypeEquipment
)
import logging

logger = logging.getLogger(__name__)

# Inline Classes
class CruiseCabinPriceInline(admin.TabularInline):
    model = CruiseCabinPrice
    extra = 1
    fields = ('cabin_type', 'price')
    autocomplete_fields = ['cabin_type']

class CruiseSessionInline(admin.StackedInline):
    model = CruiseSession
    extra = 1
    show_change_link = True
    inlines = [CruiseCabinPriceInline]

class CruiseItineraryInline(admin.TabularInline):
    model = CruiseItinerary
    extra = 1
    fields = ('day', 'port', 'arrival_time', 'departure_time', 'description')

class CabinTypeEquipmentInline(admin.TabularInline):
    model = CabinTypeEquipment
    extra = 1
    verbose_name = "Equipment"
    verbose_name_plural = "Equipment"
    autocomplete_fields = ['equipment']


# Admin Classes
@admin.register(Cruise)
class CruiseAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'cruise_type', 'company', 'get_price_range',
        'get_next_session', 'has_flyer', 'generate_flyer_button'
    )
    list_filter = ('cruise_type', 'company')
    search_fields = ('name', 'description', 'company__name')
    inlines = [CruiseSessionInline, CruiseItineraryInline]
    actions = ['duplicate_cruise']
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

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('sessions', 'cruisecabinprice_set')

    def get_price_range(self, obj):
        prices = [cp.price for cp in obj.cruisecabinprice_set.all()]
        if prices:
            min_price = localize(min(prices))
            max_price = localize(max(prices))
            return format_html("€{} - €{}", min_price, max_price)
        return "N/A"
    get_price_range.short_description = "Price Range"

    def get_next_session(self, obj):
        next_session = obj.sessions.filter(start_date__gte=timezone.now()).order_by('start_date').first()
        return next_session.start_date if next_session else "No upcoming sessions"
    get_next_session.short_description = "Next Session"

    def has_flyer(self, obj):
        return bool(obj.flyer_pdf)
    has_flyer.boolean = True
    has_flyer.short_description = "Has Flyer"

    def generate_flyer_button(self, obj):
        url = reverse('admin:cruises_cruise_generate_flyer', args=[obj.pk])
        return format_html('<a class="button" href="{}">Generate Flyer</a>', url)
    generate_flyer_button.short_description = 'Generate Flyer'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:cruise_id>/generate_flyer/',
                self.admin_site.admin_view(self.generate_flyer_view),
                name='cruises_cruise_generate_flyer'
            ),
        ]
        return custom_urls + urls

    def generate_flyer_view(self, request, cruise_id):
        cruise = self.get_object(request, cruise_id)
        try:
            pdf_content = cruise.generate_pdf_flyer()
            if pdf_content:
                filename = f"cruise_flyer_{cruise_id}.pdf"
                response = HttpResponse(pdf_content, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
            else:
                messages.error(request, "Failed to generate PDF flyer due to an unknown error.")
                logger.error("Unknown error generating PDF flyer for cruise %s", cruise_id)
        except Exception as e:
            messages.error(request, f"Failed to generate PDF flyer: {str(e)}")
            logger.exception("Error generating PDF flyer for cruise %s", cruise_id)
        return redirect('admin:cruises_cruise_change', cruise_id)

    def duplicate_cruise(self, request, queryset):
        for cruise in queryset:
            with transaction.atomic():
                new_cruise = Cruise.objects.create(
                    name=f"Copy of {cruise.name}",
                    description=cruise.description,
                    cruise_type=cruise.cruise_type,
                    company=cruise.company,
                    image=cruise.image,
                    image_url=cruise.image_url,
                    flyer_pdf=cruise.flyer_pdf
                )
                # Duplicate sessions
                session_mapping = {}
                for session in cruise.sessions.all():
                    original_session_id = session.id
                    session.pk = None
                    session.cruise = new_cruise
                    session.save()
                    session_mapping[original_session_id] = session
                # Duplicate cabin prices
                for cabin_price in cruise.cruisecabinprice_set.all():
                    cabin_price.pk = None
                    cabin_price.cruise = new_cruise
                    cabin_price.session = session_mapping.get(cabin_price.session_id)
                    cabin_price.save()
                # Duplicate itineraries
                for itinerary in cruise.itineraries.all():
                    itinerary.pk = None
                    itinerary.cruise = new_cruise
                    itinerary.save()
        self.message_user(request, f"{len(queryset)} cruise(s) duplicated successfully.")
    duplicate_cruise.short_description = "Duplicate selected cruises"

@admin.register(CruiseSession)
class CruiseSessionAdmin(admin.ModelAdmin):
    list_display = ('cruise', 'start_date', 'end_date', 'capacity', 'get_cabin_prices')
    list_filter = ('cruise', 'start_date')
    search_fields = ('cruise__name',)
    inlines = [CruiseCabinPriceInline]

    def get_cabin_prices(self, obj):
        prices = obj.cabin_prices.select_related('cabin_type').all()
        return ", ".join([f"{price.cabin_type.name}: €{price.price}" for price in prices])
    get_cabin_prices.short_description = "Cabin Prices"


@admin.register(CabinType)
class CabinTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity', 'deck', 'get_cruise_count', 'get_equipment_summary')
    search_fields = ('name', 'description')
    inlines = [CabinTypeEquipmentInline]

    def get_cruise_count(self, obj):
        return obj.cruisecabinprice_set.values('cruise').distinct().count()
    get_cruise_count.short_description = "Number of Cruises"

    def get_equipment_summary(self, obj):
        equipment_list = obj.cabintypeequipment_set.select_related('equipment').all()
        return ", ".join([f"{item.equipment.name} (x{item.quantity})" for item in equipment_list])
    get_equipment_summary.short_description = "Equipment"




@admin.register(CruiseCabinPrice)
class CruiseCabinPriceAdmin(admin.ModelAdmin):
    list_display = ('cruise', 'cabin_type', 'price', 'session')
    list_filter = ('cruise', 'cabin_type', 'session')
    search_fields = ('cruise__name', 'cabin_type__name')

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')

@admin.register(CabinTypeEquipment)
class CabinTypeEquipmentAdmin(admin.ModelAdmin):
    list_display = ('cabin_type', 'equipment', 'quantity')
    list_filter = ('cabin_type', 'equipment')
    search_fields = ('cabin_type__name', 'equipment__name')

@admin.register(CruiseCompany)
class CruiseCompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'website')
    search_fields = ('name',)

@admin.register(CruiseType)
class CruiseTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'website', 'featured')
    list_filter = ('featured',)
    search_fields = ('name',)

@admin.register(Port)
class PortAdmin(admin.ModelAdmin):
    list_display = ('name', 'country')
    search_fields = ('name', 'country')

@admin.register(Excursion)
class ExcursionAdmin(admin.ModelAdmin):
    list_display = ('name', 'port', 'duration', 'price')
    search_fields = ('name', 'port__name')
    list_filter = ('port',)
