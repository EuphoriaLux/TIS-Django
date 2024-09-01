from django import forms
from django.contrib import admin
from django.db.models import Sum, Min, Max, Count
from django.utils import timezone
from django.urls import reverse
from django.utils.html import format_html
from django.urls import path
from django.http import HttpResponse, FileResponse
from django.contrib import messages
from django.shortcuts import redirect
from .models import CruiseCompany, CruiseType, Brand, Cruise, CruiseSession, Equipment, CabinType, CruiseCabinPrice, CruiseItinerary, Port, Excursion, CabinTypeEquipment
import logging

logger = logging.getLogger(__name__)

class CruiseSessionInline(admin.TabularInline):
    model = CruiseSession
    extra = 1
    min_num = 1
    fields = ('start_date', 'end_date', 'capacity', 'is_summer_special', 'summer_special_type')

class CruiseCabinPriceInline(admin.TabularInline):
    model = CruiseCabinPrice
    extra = 1
    min_num = 1
    fields = ('cabin_type', 'price', 'session')

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

class CabinTypeAdminForm(forms.ModelForm):
    equipment = forms.ModelMultipleChoiceField(
        queryset=Equipment.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = CabinType
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['equipment'].initial = self.instance.equipment.all()

    def save(self, commit=True):
        cabin_type = super().save(commit=False)
        if commit:
            cabin_type.save()
        if 'equipment' in self.cleaned_data:
            equipment = self.cleaned_data['equipment']
            CabinTypeEquipment.objects.filter(cabin_type=cabin_type).delete()
            for equip in equipment:
                CabinTypeEquipment.objects.create(cabin_type=cabin_type, equipment=equip)
        return cabin_type

@admin.register(Cruise)
class CruiseAdmin(admin.ModelAdmin):
    list_display = ('name', 'cruise_type', 'company', 'get_price_range', 'get_next_session', 'get_total_capacity', 'has_flyer', 'generate_flyer_button')
    list_filter = ('cruise_type', 'company', 'sessions__start_date')
    search_fields = ('name', 'description', 'company__name')
    inlines = [CruiseSessionInline, CruiseCabinPriceInline, CruiseItineraryInline]
    readonly_fields = ('get_total_capacity',)
    actions = ['duplicate_cruise']
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'cruise_type', 'company', 'get_total_capacity')
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
        prices = CruiseCabinPrice.objects.filter(cruise=obj)
        if prices.exists():
            price_range = prices.aggregate(min_price=Min('price'), max_price=Max('price'))
            return f"€{price_range['min_price']} - €{price_range['max_price']}"
        return "N/A"
    get_price_range.short_description = "Price Range"

    def get_next_session(self, obj):
        next_session = obj.sessions.filter(start_date__gte=timezone.now()).order_by('start_date').first()
        return next_session.start_date if next_session else "No upcoming sessions"
    get_next_session.short_description = "Next Session"

    def get_total_capacity(self, obj):
        return obj.sessions.aggregate(total_capacity=Sum('capacity'))['total_capacity'] or 0
    get_total_capacity.short_description = "Total Capacity"

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
            path('<int:cruise_id>/generate_flyer/', self.admin_site.admin_view(self.generate_flyer_view), name='cruises_cruise_generate_flyer'),
        ]
        return custom_urls + urls

    def generate_flyer_view(self, request, cruise_id):
        cruise = self.get_object(request, cruise_id)
        pdf_content = cruise.generate_pdf_flyer()
        
        if pdf_content:
            filename = f"cruise_flyer_{cruise_id}.pdf"
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        else:
            messages.error(request, "Failed to generate PDF flyer.")
            return redirect('admin:cruises_cruise_change', cruise_id)

    def duplicate_cruise(self, request, queryset):
        for cruise in queryset:
            new_cruise = Cruise.objects.create(
                name=f"Copy of {cruise.name}",
                description=cruise.description,
                cruise_type=cruise.cruise_type,
                company=cruise.company,
                image=cruise.image,
                image_url=cruise.image_url
            )
            for session in cruise.sessions.all():
                CruiseSession.objects.create(
                    cruise=new_cruise,
                    start_date=session.start_date,
                    end_date=session.end_date,
                    capacity=session.capacity,
                    is_summer_special=session.is_summer_special,
                    summer_special_type=session.summer_special_type
                )
            for cabin_price in cruise.cruisecabinprice_set.all():
                CruiseCabinPrice.objects.create(
                    cruise=new_cruise,
                    cabin_type=cabin_price.cabin_type,
                    price=cabin_price.price,
                    session=new_cruise.sessions.first()
                )
            for itinerary in cruise.itineraries.all():
                CruiseItinerary.objects.create(
                    cruise=new_cruise,
                    day=itinerary.day,
                    port=itinerary.port,
                    arrival_time=itinerary.arrival_time,
                    departure_time=itinerary.departure_time,
                    description=itinerary.description
                )
        self.message_user(request, f"{len(queryset)} cruise(s) duplicated successfully.")
    duplicate_cruise.short_description = "Duplicate selected cruises"

@admin.register(CruiseSession)
class CruiseSessionAdmin(admin.ModelAdmin):
    list_display = ('cruise', 'start_date', 'end_date', 'capacity', 'is_summer_special', 'get_cabin_prices')
    list_filter = ('cruise', 'start_date', 'is_summer_special')
    search_fields = ('cruise__name',)

    def get_cabin_prices(self, obj):
        prices = CruiseCabinPrice.objects.filter(session=obj)
        return ", ".join([f"{price.cabin_type.name}: €{price.price}" for price in prices])
    get_cabin_prices.short_description = "Cabin Prices"

@admin.register(CabinType)
class CabinTypeAdmin(admin.ModelAdmin):
    form = CabinTypeAdminForm
    list_display = ('name', 'capacity', 'deck', 'get_cruise_count', 'get_equipment_summary')
    search_fields = ('name', 'description')
    inlines = [CabinTypeEquipmentInline]

    def get_cruise_count(self, obj):
        return obj.cruisecabinprice_set.values('cruise').distinct().count()
    get_cruise_count.short_description = "Number of Cruises"

    def get_equipment_summary(self, obj):
        equipment = obj.cabintypeequipment_set.all()
        return ", ".join([f"{e.equipment.name} (x{e.quantity})" for e in equipment])
    get_equipment_summary.short_description = "Equipment"

@admin.register(CruiseCabinPrice)
class CruiseCabinPriceAdmin(admin.ModelAdmin):
    list_display = ('cruise', 'cabin_type', 'price', 'session')
    list_filter = ('cruise', 'cabin_type', 'session')
    search_fields = ('cruise__name', 'cabin_type__name')

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'name_de', 'name_fr')
    search_fields = ('name', 'description', 'name_de', 'name_fr')

@admin.register(CabinTypeEquipment)
class CabinTypeEquipmentAdmin(admin.ModelAdmin):
    list_display = ('cabin_type', 'equipment', 'quantity')
    list_filter = ('cabin_type', 'equipment')
    search_fields = ('cabin_type__name', 'equipment__name')

# Register other models as needed
admin.site.register(CruiseCompany)
admin.site.register(CruiseType)
admin.site.register(Brand)
admin.site.register(Port)
admin.site.register(Excursion)