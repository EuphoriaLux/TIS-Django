# bookings/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.contrib import messages

from .models import (
    Booking,
    Passenger,
    BookingAdditionalService,
    ExcursionBooking  # Updated name
)

class PassengerInline(admin.StackedInline):
    model = Passenger
    extra = 0
    fields = (
        ('first_name', 'last_name'),
        ('email', 'phone'),
        ('date_of_birth', 'nationality'),
        ('passport_number', 'passport_expiry_date', 'passport_issued_country'),
        ('dietary_requirements', 'medical_requirements'),
        'is_lead_passenger'
    )

class BookingAdditionalServiceInline(admin.TabularInline):
    model = BookingAdditionalService
    extra = 0
    fields = (
        'service_type',
        'service_name',
        'description',
        'price',
        'quantity',
        'is_per_person',
        'total_price'
    )
    readonly_fields = ('total_price',)

class ExcursionBookingInline(admin.TabularInline):
    model = ExcursionBooking
    extra = 0
    fields = (
        'cruise_excursion',
        'special_requirements',
        'pickup_location',
        'total_price'
    )
    readonly_fields = ('total_price',)
    raw_id_fields = ('cruise_excursion',)
    filter_horizontal = ('passengers',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'quote_link',
        'cruise_link',
        'cabin_link',
        'lead_passenger',
        'status',
        'payment_status',
        'price_display',
        'passenger_count',
        'created_at'
    )
    list_filter = (
        'status',
        'payment_status',
        'cruise_session__cruise__ship',
        'cruise_session__start_date',
        'created_at'
    )
    search_fields = (
        'user__username',
        'cruise_session__cruise__name',
        'passengers__first_name',
        'passengers__last_name',
        'confirmation_number'
    )
    inlines = [
        PassengerInline,
        BookingAdditionalServiceInline,
        ExcursionBookingInline
    ]
    readonly_fields = (
        'created_at',
        'updated_at',
        'confirmation_number',
        'total_price',
        'amount_paid',
        'balance_due'
    )
    fieldsets = (
        (None, {
            'fields': (
                'user',
                'quote',
                'cruise_session',
                'cabin_category',
                'confirmation_number'
            )
        }),
        (_('Status'), {
            'fields': (
                'status',
                'payment_status',
                'cancellation_reason'
            )
        }),
        (_('Pricing'), {
            'fields': (
                'base_price',
                ('applied_promotion', 'discount_amount'),
                'total_price',
                'amount_paid',
                'balance_due'
            )
        }),
        (_('Additional Information'), {
            'fields': (
                'special_requests',
                'internal_notes',
                ('created_at', 'updated_at')
            )
        })
    )
    raw_id_fields = ('quote', 'cruise_session', 'cabin_category', 'applied_promotion')

    def cruise_link(self, obj):
        url = reverse("admin:cruises_cruise_change", args=[obj.cruise_session.cruise.id])
        return format_html('<a href="{}">{}</a>', url, obj.cruise_session.cruise.name)
    cruise_link.short_description = _('Cruise')

    def cabin_link(self, obj):
        url = reverse("admin:cruises_cabincategory_change", args=[obj.cabin_category.id])
        return format_html('<a href="{}">{}</a>', url, obj.cabin_category.name)
    cabin_link.short_description = _('Cabin')

    def lead_passenger(self, obj):
        passenger = obj.passengers.filter(is_lead_passenger=True).first()
        return passenger.full_name if passenger else _("No lead passenger")
    lead_passenger.short_description = _('Lead Passenger')

    def price_display(self, obj):
        return format_html(
            """Base: €{}<br>
            Paid: €{}<br>
            Balance: €{}""",
            obj.total_price,
            obj.amount_paid,
            obj.balance_due
        )
    price_display.short_description = _('Price Details')

    def quote_link(self, obj):
        if obj.quote:
            url = reverse("admin:quotes_quote_change", args=[obj.quote.id])
            return format_html('<a href="{}">Quote {}</a>', url, obj.quote.id)
        return _('No Quote')
    quote_link.short_description = _('Quote')

    actions = ['mark_as_paid', 'mark_as_confirmed', 'cancel_bookings']

    @admin.action(description=_("Mark selected bookings as paid"))
    def mark_as_paid(self, request, queryset):
        updated = 0
        for booking in queryset:
            if booking.balance_due > 0:
                booking.record_payment(booking.balance_due)
                updated += 1
        self.message_user(
            request,
            _("%(count)d booking(s) marked as paid.") % {'count': updated},
            messages.SUCCESS
        )

    @admin.action(description=_("Mark selected bookings as confirmed"))
    def mark_as_confirmed(self, request, queryset):
        updated = queryset.filter(status=Booking.Status.PENDING).update(
            status=Booking.Status.CONFIRMED
        )
        self.message_user(
            request,
            _("%(count)d booking(s) marked as confirmed.") % {'count': updated},
            messages.SUCCESS
        )

    @admin.action(description=_("Cancel selected bookings"))
    def cancel_bookings(self, request, queryset):
        updated = 0
        for booking in queryset:
            if booking.status not in [Booking.Status.CANCELLED, Booking.Status.COMPLETED]:
                booking.cancel()
                updated += 1
        self.message_user(
            request,
            _("%(count)d booking(s) cancelled.") % {'count': updated},
            messages.SUCCESS
        )

@admin.register(Passenger)
class PassengerAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'booking_link',
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
        'booking__confirmation_number'
    )
    raw_id_fields = ('booking',)

    def booking_link(self, obj):
        url = reverse("admin:bookings_booking_change", args=[obj.booking.id])
        return format_html('<a href="{}">{}</a>', url, obj.booking.confirmation_number or f'Booking {obj.booking.id}')
    booking_link.short_description = _('Booking')

@admin.register(BookingAdditionalService)
class BookingAdditionalServiceAdmin(admin.ModelAdmin):
    list_display = (
        'service_name',
        'service_type',
        'booking_link',
        'price',
        'quantity',
        'is_per_person',
        'total_price'
    )
    list_filter = ('service_type', 'is_per_person')
    search_fields = (
        'service_name',
        'booking__confirmation_number',
        'booking__passengers__first_name',
        'booking__passengers__last_name'
    )
    raw_id_fields = ('booking',)

    def booking_link(self, obj):
        url = reverse("admin:bookings_booking_change", args=[obj.booking.id])
        return format_html('<a href="{}">{}</a>', url, obj.booking.confirmation_number or f'Booking {obj.booking.id}')
    booking_link.short_description = _('Booking')

@admin.register(ExcursionBooking)
class ExcursionBookingAdmin(admin.ModelAdmin):
    list_display = (
        'excursion_name',
        'booking_link',
        'available_date',
        'departure_time',
        'passenger_count',
        'total_price'
    )
    list_filter = (
        'cruise_excursion__excursion__port',
        'cruise_excursion__available_date'
    )
    search_fields = (
        'cruise_excursion__excursion__name',
        'booking__confirmation_number',
        'special_requirements'
    )
    raw_id_fields = ('booking', 'cruise_excursion')
    filter_horizontal = ('passengers',)

    def booking_link(self, obj):
        url = reverse("admin:bookings_booking_change", args=[obj.booking.id])
        return format_html('<a href="{}">{}</a>', url, obj.booking.confirmation_number or f'Booking {obj.booking.id}')
    booking_link.short_description = _('Booking')

    def excursion_name(self, obj):
        return obj.cruise_excursion.excursion.name
    excursion_name.short_description = _('Excursion')

    def available_date(self, obj):
        return obj.cruise_excursion.available_date
    available_date.short_description = _('Date')

    def departure_time(self, obj):
        return obj.cruise_excursion.departure_time
    departure_time.short_description = _('Time')

    def passenger_count(self, obj):
        return obj.passengers.count()
    passenger_count.short_description = _('Passengers')