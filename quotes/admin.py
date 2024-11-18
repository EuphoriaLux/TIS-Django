# quotes/admin.py

from django.contrib import admin, messages
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _

from .models import Quote, QuotePassenger, QuoteAdditionalService
from .utils import generate_quote_pdf
from .views import convert_quote_to_booking


class QuotePassengerInline(admin.StackedInline):
    model = QuotePassenger
    extra = 0
    fields = (
        ('first_name', 'last_name'),
        ('email', 'phone'),
        ('date_of_birth', 'nationality'),
        ('passport_number', 'passport_expiry_date'),
        'dietary_requirements',
        'medical_requirements'
    )

class QuoteAdditionalServiceInline(admin.TabularInline):
    model = QuoteAdditionalService
    extra = 11
    fields = ('service_type', 'service_name', 'description', 'price', 'quantity')

@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'passenger_display',
        'cruise_session',
        'cabin_category',
        'get_price_display',
        'status',
        'expiration_date',
        'booking_link',
        'actions_display'
    )
    list_filter = (
        'status',
        'created_at',
        'cruise_session__cruise__ship',
        'cabin_category__ship'
    )
    search_fields = (
        'passengers__first_name',
        'passengers__last_name',
        'passengers__email',
        'cruise_session__cruise__name',
        'cabin_category__name'
    )
    readonly_fields = (
        'total_price',
        'base_price',
        'discount_amount',
        'booking_link'
    )
    inlines = [QuotePassengerInline, QuoteAdditionalServiceInline]
    fieldsets = (
        (None, {
            'fields': (
                'user',
                'cruise_session',
                'cabin_category',
                'status'
            )
        }),
        (_('Pricing'), {
            'fields': (
                'number_of_passengers',
                'base_price',
                'applied_promotion',
                'discount_amount',
                'total_price'
            )
        }),
        (_('Quote Details'), {
            'fields': (
                'cancellation_policy',
                'expiration_date',
                'note'
            )
        })
    )
    raw_id_fields = ('cruise_session', 'cabin_category', 'applied_promotion')

    def get_price_display(self, obj):
        return format_html(
            """Base: €{}<br>
            Discount: €{}<br>
            Total: €{}""",
            obj.base_price,
            obj.discount_amount,
            obj.total_price
        )
    get_price_display.short_description = _("Price Details")

    def booking_link(self, obj):
        if hasattr(obj, 'booking'):
            url = reverse("admin:bookings_booking_change", args=[obj.booking.id])
            return format_html('<a href="{}">Booking {}</a>', url, obj.booking.id)
        return _('No Booking')
    booking_link.short_description = _('Booking')

    def passenger_display(self, obj):
        passenger = obj.passengers.first()
        if passenger:
            return f"{passenger.full_name}"
        return _("No passenger")
    passenger_display.short_description = _('Lead Passenger')

    def actions_display(self, obj):
        buttons = []
        
        # Generate Quote PDF button
        quote_url = reverse('admin:generate_quote', args=[obj.pk])
        buttons.append(
            f'<a class="button" href="{quote_url}">{_("Generate PDF")}</a>'
        )
        
        # Convert to Booking button (if applicable)
        if obj.can_convert_to_booking():
            convert_url = reverse('admin:convert_quote_to_booking', args=[obj.pk])
            buttons.append(
                f'<a class="button" href="{convert_url}">{_("Convert to Booking")}</a>'
            )
        
        return format_html('&nbsp;'.join(buttons))
    actions_display.short_description = _('Actions')

    def generate_quote_view(self, request, quote_id):
        quote = get_object_or_404(Quote, id=quote_id)
        try:
            pdf = generate_quote_pdf(quote)
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="quote_{quote.id}.pdf"'
            return response
        except Exception as e:
            self.message_user(request, f"Error generating PDF: {str(e)}", messages.ERROR)
            return redirect('admin:quotes_quote_change', quote_id)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'create-quote/<int:quote_id>/',
                self.admin_site.admin_view(self.generate_quote_view),
                name='generate_quote'
            ),
            path(
                '<int:quote_id>/convert/',
                self.admin_site.admin_view(convert_quote_to_booking),
                name='convert_quote_to_booking'
            ),
        ]
        return custom_urls + urls
    
    actions = ['convert_to_booking']

    def convert_to_booking(self, request, queryset):
        converted = 0
        for quote in queryset:
            if quote.can_convert_to_booking():
                try:
                    booking = quote.convert_to_booking()
                    converted += 1
                    self.message_user(
                        request,
                        _("Quote %(quote)s successfully converted to Booking %(booking)s") % {
                            'quote': quote.id,
                            'booking': booking.id
                        },
                        messages.SUCCESS
                    )
                except Exception as e:
                    self.message_user(
                        request,
                        _("Error converting Quote %(quote)s to Booking: %(error)s") % {
                            'quote': quote.id,
                            'error': str(e)
                        },
                        messages.ERROR
                    )
            else:
                self.message_user(
                    request,
                    _("Quote %(quote)s cannot be converted to a booking.") % {
                        'quote': quote.id
                    },
                    messages.WARNING
                )
        
        if converted:
            self.message_user(
                request,
                _("%(count)d quote(s) were converted to bookings.") % {
                    'count': converted
                },
                messages.SUCCESS
            )
    convert_to_booking.short_description = _("Convert selected quotes to bookings")

@admin.register(QuotePassenger)
class QuotePassengerAdmin(admin.ModelAdmin):
    list_display = (
        'get_full_name',  # Changed from full_name
        'email',
        'phone',
        'nationality',
        'passport_number',
        'is_lead_passenger'
    )
    list_filter = ('nationality', 'is_lead_passenger')
    search_fields = (
        'first_name',
        'last_name',
        'email',
        'passport_number',
        'quote__confirmation_number'
    )
    raw_id_fields = ('quote',)

    def get_full_name(self, obj):
        """Return the passenger's full name"""
        return f"{obj.first_name} {obj.last_name}"
    get_full_name.short_description = _('Full Name')

@admin.register(QuoteAdditionalService)
class QuoteAdditionalServiceAdmin(admin.ModelAdmin):
    list_display = (
        'service_name',
        'service_type',
        'quote',
        'price',
        'quantity',
        'total_price'
    )
    list_filter = ('service_type',)
    search_fields = (
        'service_name',
        'description',
        'quote__passengers__first_name',
        'quote__passengers__last_name'
    )
    raw_id_fields = ('quote',)