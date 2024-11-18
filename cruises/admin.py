# cruises/admin.py
import nested_admin
from django import forms
from django.contrib import admin
from django.db import transaction
from django.utils import timezone
from django.utils.formats import localize
from django.urls import reverse, path
from django.utils.html import format_html
from django.http import HttpResponse
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _

from .models import (
    Location,
    Port,
    CruiseCompany,
    Brand,
    Region,
    Ship,
    CruiseType,
    Cruise,
    CruiseSession,
    CabinCategory,
    Equipment,
    CabinEquipment,
    Excursion,
    CruiseExcursion,
    CruiseSessionCabinPrice,
    Promotion
)

import logging
logger = logging.getLogger(__name__)

# Nested Inline Classes
class CabinEquipmentInline(nested_admin.NestedTabularInline):
    model = CabinEquipment  # Updated from CabinTypeEquipment to CabinEquipment
    extra = 1
    verbose_name = _("Equipment")
    verbose_name_plural = _("Equipment")
    autocomplete_fields = ['equipment']

class CruiseSessionCabinPriceInline(nested_admin.NestedTabularInline):
    model = CruiseSessionCabinPrice
    extra = 1
    fields = (
        'cabin_category',
        'price',
        'regular_price',
        'is_early_bird',
        'early_bird_deadline',
        'single_supplement',
        'third_person_discount',
        'available_cabins',
        'get_current_price_display',
        'get_availability_status'
    )
    readonly_fields = ('get_current_price_display', 'get_availability_status')
    autocomplete_fields = ['cabin_category']
    
    def get_current_price_display(self, obj):
        if obj and obj.pk:
            return format_html(
                '€{} {}',
                localize(obj.get_current_price()),
                '<small>(Early Bird)</small>' if obj.is_early_bird and obj.early_bird_deadline and timezone.now().date() <= obj.early_bird_deadline else ''
            )
        return '-'
    get_current_price_display.short_description = _("Current Price")

    def get_availability_status(self, obj):
        if obj and obj.pk:
            if not obj.is_available:
                return format_html('<span style="color: red;">Sold Out</span>')
            if obj.available_cabins <= 5:
                return format_html('<span style="color: orange;">{} left</span>', obj.available_cabins)
            return format_html('<span style="color: green;">{} available</span>', obj.available_cabins)
        return '-'
    get_availability_status.short_description = _("Availability")

@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('name', 'promotion_type', 'discount_type', 'discount_value', 'start_date', 'end_date', 'is_active')
    list_filter = ('promotion_type', 'discount_type', 'start_date', 'end_date')
    search_fields = ('name', 'description', 'terms_conditions')
    ordering = ('-start_date',)

    def is_active(self, obj):
        return obj.is_active()
    is_active.boolean = True
    is_active.short_description = _("Is Active")

class CruiseSessionInline(nested_admin.NestedStackedInline):
    model = CruiseSession
    extra = 1
    show_change_link = True
    fields = (
        ('start_date', 'end_date'),
        ('embarkation_port', 'disembarkation_port'),
        'capacity',
        'status',
        'promotion'
    )
    raw_id_fields = ['promotion']  # Changed from autocomplete_fields to raw_id_fields
    autocomplete_fields = ['embarkation_port', 'disembarkation_port']

class CruiseExcursionInline(nested_admin.NestedTabularInline):
    model = CruiseExcursion
    extra = 1
    fields = ('excursion', 'available_date', 'departure_time', 'available_spots', 'price_override')
    autocomplete_fields = ['excursion']

# Admin Classes
@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'timezone')
    list_filter = ('country',)
    search_fields = ('name', 'country')

@admin.register(Port)
class PortAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'port_code', 'is_embarkation_port', 'is_disembarkation_port')
    list_filter = ('country', 'is_embarkation_port', 'is_disembarkation_port')
    search_fields = ('name', 'country', 'port_code')

@admin.register(CruiseCompany)
class CruiseCompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'website', 'fleet_size', 'get_regions')
    search_fields = ('name', 'description')
    filter_horizontal = ('operating_regions',)

    def get_regions(self, obj):
        return ", ".join(region.name for region in obj.operating_regions.all())
    get_regions.short_description = _("Operating Regions")

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent_company', 'market_segment', 'featured')
    list_filter = ('market_segment', 'featured', 'parent_company')
    search_fields = ('name', 'description')

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent_region', 'get_ports_count')
    list_filter = ('parent_region',)
    search_fields = ('name', 'description')
    filter_horizontal = ('ports',)

    def get_ports_count(self, obj):
        return obj.ports.count()
    get_ports_count.short_description = _("Number of Ports")

@admin.register(Ship)
class ShipAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'brand', 'year_built', 'passenger_capacity')
    list_filter = ('company', 'brand', 'year_built')
    search_fields = ('name', 'company__name', 'brand__name')
    readonly_fields = ('get_cabin_categories',)

    def get_cabin_categories(self, obj):
        categories = obj.cabin_categories.all()
        return format_html("<br>".join(
            f"{cat.name} ({cat.category_code}) - Capacity: {cat.capacity}" 
            for cat in categories
        ))
    get_cabin_categories.short_description = _("Cabin Categories")

@admin.register(Cruise)
class CruiseAdmin(nested_admin.NestedModelAdmin):
    list_display = (
        'name',
        'ship',
        'cruise_type',
        'get_company',
        'get_price_range',
        'get_next_available_session',
        'get_session_count',
        'get_duration',
        'is_featured'
    )
    list_filter = (
        'cruise_type', 
        'ship__company',
        'is_featured',
        'difficulty_level'
    )
    search_fields = (
        'name',
        'description',
        'ship__name',
        'ship__company__name'
    )
    filter_horizontal = ('regions',)
    inlines = [CruiseSessionInline, CruiseExcursionInline]
    actions = ['duplicate_cruise']

    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'cruise_type', 'ship', 'regions')
        }),
        (_('Visibility and Difficulty'), {
            'fields': ('is_featured', 'difficulty_level'),
        }),
        (_('Media'), {
            'fields': ('image', 'image_url', 'flyer_pdf'),
            'classes': ('collapse',)
        }),
    )

    def get_next_available_session(self, obj):
        next_session = obj.get_upcoming_sessions().first()
        if next_session:
            return format_html(
                '{} <br/><small>({})</small>',
                next_session.start_date,
                next_session.get_status_display()
            )
        return "No upcoming sessions"
    get_next_available_session.short_description = "Next Session"

    def get_company(self, obj):
        return obj.ship.company
    get_company.short_description = _("Company")
    get_company.admin_order_field = 'ship__company'

    def get_session_count(self, obj):
        active = obj.get_active_sessions().count()
        total = obj.get_session_count()
        return f"{active} active / {total} total"
    get_session_count.short_description = "Sessions"

    def get_duration(self, obj):
        return obj.duration_range
    get_duration.short_description = "Duration"

    def get_price_range(self, obj):
        min_price, max_price = obj.price_range
        if min_price is not None and max_price is not None:
            return format_html("€{} - €{}", localize(min_price), localize(max_price))
        return _("N/A")
    get_price_range.short_description = _("Price Range")

    @admin.action(description=_("Duplicate selected cruises"))
    def duplicate_cruise(self, request, queryset):
        for cruise in queryset:
            with transaction.atomic():
                # Create new cruise
                new_cruise = Cruise.objects.create(
                    name=f"Copy of {cruise.name}",
                    description=cruise.description,
                    cruise_type=cruise.cruise_type,
                    ship=cruise.ship,
                    image=cruise.image,
                    image_url=cruise.image_url,
                    flyer_pdf=cruise.flyer_pdf,
                    is_featured=False,
                    difficulty_level=cruise.difficulty_level
                )
                
                # Copy regions
                new_cruise.regions.set(cruise.regions.all())
                
                # Copy sessions and their cabin prices
                for session in cruise.sessions.all():
                    old_session = session
                    session.pk = None
                    session.cruise = new_cruise
                    session.save()
                    
                    # Copy cabin prices
                    for cabin_price in old_session.cabin_prices.all():
                        cabin_price.pk = None
                        cabin_price.cruise_session = session
                        cabin_price.save()
                
                # Copy excursions
                for excursion in cruise.excursions.all():
                    excursion.pk = None
                    excursion.cruise = new_cruise
                    excursion.save()
                    
        self.message_user(
            request,
            _("%(count)d cruise(s) duplicated successfully.") % {'count': len(queryset)}
        )


@admin.register(CruiseSession)
class CruiseSessionAdmin(admin.ModelAdmin):
    list_display = (
        'cruise',
        'start_date',
        'end_date',
        'status',
        'get_duration',
        'get_price_range'
    )
    list_filter = (
        'cruise__ship',
        'status',
        'start_date'
    )
    search_fields = (
        'cruise__name',
        'cruise__ship__name'
    )
    raw_id_fields = (
        'cruise',
        'embarkation_port',
        'disembarkation_port'
    )
    date_hierarchy = 'start_date'
    inlines = [CruiseSessionCabinPriceInline]

    def get_duration(self, obj):
        return f"{obj.duration} days"
    get_duration.short_description = _("Duration")

    def get_price_range(self, obj):
        prices = obj.cabin_prices.all()
        if not prices:
            return _("No prices set")
        
        current_prices = [price.get_current_price() for price in prices]
        min_price = min(current_prices)
        max_price = max(current_prices)
        
        if min_price == max_price:
            return format_html('€{}', localize(min_price))
        return format_html('€{} - €{}', localize(min_price), localize(max_price))
    get_price_range.short_description = _("Price Range")

@admin.register(CabinCategory)
class CabinCategoryAdmin(nested_admin.NestedModelAdmin):
    list_display = ('name', 'ship', 'category_code', 'deck', 'capacity', 'square_meters')
    list_filter = ('ship', 'deck', 'has_balcony', 'is_accessible')
    search_fields = ('name', 'category_code', 'ship__name')
    inlines = [CabinEquipmentInline]
    exclude = ('equipment',)  # Exclude since we're using the through model


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_de', 'name_fr')
    search_fields = ('name', 'name_de', 'name_fr')

@admin.register(Excursion)
class ExcursionAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'port', 'duration', 'difficulty_level', 
        'price', 'maximum_participants', 'is_accessible'
    )
    list_filter = ('port', 'difficulty_level', 'is_accessible', 'includes_transport')
    search_fields = ('name', 'description', 'port__name')
    raw_id_fields = ('port',)

@admin.register(CruiseExcursion)
class CruiseExcursionAdmin(admin.ModelAdmin):
    list_display = (
        'excursion', 'cruise', 'available_date', 
        'departure_time', 'available_spots', 'current_price'
    )
    list_filter = ('cruise', 'available_date', 'excursion__port')
    search_fields = ('excursion__name', 'cruise__name')
    raw_id_fields = ('cruise', 'excursion')
    date_hierarchy = 'available_date'

@admin.register(CruiseSessionCabinPrice)
class CruiseSessionCabinPriceAdmin(admin.ModelAdmin):
    list_display = (
        'cabin_category',
        'cruise_session',
        'get_current_price_display',
        'regular_price',
        'is_early_bird',
        'early_bird_deadline',
        'available_cabins',
        'get_availability_status',
        'get_price_details'
    )
    
    list_filter = (
        'is_early_bird',
        'cruise_session__cruise__ship',
        'cruise_session__status',
        'cabin_category__deck',
        ('early_bird_deadline', admin.DateFieldListFilter),
    )
    
    search_fields = (
        'cruise_session__cruise__name',
        'cabin_category__name',
        'cabin_category__category_code'
    )
    
    readonly_fields = (
        'get_current_price_display',
        'get_single_price_display',
        'get_third_person_price_display',
        'get_availability_status'
    )
    
    fieldsets = (
        (None, {
            'fields': (
                'cruise_session',
                'cabin_category',
            )
        }),
        (_('Pricing'), {
            'fields': (
                'price',
                'regular_price',
                'get_current_price_display',
                'get_single_price_display',
                'get_third_person_price_display',
            )
        }),
        (_('Early Bird Offer'), {
            'fields': (
                'is_early_bird',
                'early_bird_deadline',
            ),
        }),
        (_('Supplements and Discounts'), {
            'fields': (
                'single_supplement',
                'third_person_discount',
            )
        }),
        (_('Availability'), {
            'fields': (
                'available_cabins',
                'get_availability_status',
            )
        }),
    )

    def get_current_price_display(self, obj):
        current_price = obj.get_current_price()
        if obj.is_early_bird and obj.early_bird_deadline:
            if timezone.now().date() <= obj.early_bird_deadline:
                return format_html(
                    '<span style="color: green;">€{} <small>(Early Bird)</small></span>',
                    localize(current_price)
                )
        return format_html('€{}', localize(current_price))
    get_current_price_display.short_description = _("Current Price")

    def get_single_price_display(self, obj):
        single_price = obj.get_single_price()
        return format_html(
            '€{} <small>(+{}%)</small>',
            localize(single_price),
            obj.single_supplement
        )
    get_single_price_display.short_description = _("Single Price")

    def get_third_person_price_display(self, obj):
        third_person_price = obj.get_third_person_price()
        return format_html(
            '€{} <small>(-{}%)</small>',
            localize(third_person_price),
            obj.third_person_discount
        )
    get_third_person_price_display.short_description = _("Third Person Price")

    def get_availability_status(self, obj):
        if not obj.is_available:
            return format_html(
                '<span style="color: red;"><i class="fas fa-times-circle"></i> Sold Out</span>'
            )
        if obj.available_cabins <= 5:
            return format_html(
                '<span style="color: orange;"><i class="fas fa-exclamation-triangle"></i> Only {} left</span>',
                obj.available_cabins
            )
        return format_html(
            '<span style="color: green;"><i class="fas fa-check-circle"></i> {} available</span>',
            obj.available_cabins
        )
    get_availability_status.short_description = _("Availability")

    def get_price_details(self, obj):
        current_price = obj.get_current_price()
        single_price = obj.get_single_price()
        third_person_price = obj.get_third_person_price()
        
        return format_html(
            """
            <div style="white-space: nowrap;">
                <strong>Current:</strong> €{}<br>
                <strong>Single:</strong> €{}<br>
                <strong>3rd Person:</strong> €{}
            </div>
            """,
            localize(current_price),
            localize(single_price),
            localize(third_person_price)
        )
    get_price_details.short_description = _("Price Details")

    class Media:
        css = {
            'all': [
                'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css'
            ]
        }