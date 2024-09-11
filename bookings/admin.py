# bookings/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Booking, Passenger, BookingAdditionalService, BookingExcursion

class PassengerInline(admin.TabularInline):
    model = Passenger
    extra = 0

class BookingAdditionalServiceInline(admin.TabularInline):
    model = BookingAdditionalService
    extra = 0

class BookingExcursionInline(admin.TabularInline):
    model = BookingExcursion
    extra = 0

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'cruise_link', 'user', 'status', 'total_price', 'is_paid', 'passenger_count', 'created_at')
    list_filter = ('status', 'is_paid', 'cruise_session__cruise', 'created_at')
    search_fields = ('user__username', 'cruise_session__cruise__name', 'passengers__first_name', 'passengers__last_name')
    inlines = [PassengerInline, BookingAdditionalServiceInline, BookingExcursionInline]
    readonly_fields = ('created_at', 'updated_at')

    def cruise_link(self, obj):
        url = reverse("admin:cruises_cruise_change", args=[obj.cruise_session.cruise.id])
        return format_html('<a href="{}">{}</a>', url, obj.cruise_session.cruise.name)
    cruise_link.short_description = 'Cruise'

    def passenger_count(self, obj):
        return obj.passenger_count
    passenger_count.short_description = 'Passengers'

@admin.register(Passenger)
class PassengerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'booking_link', 'email', 'phone', 'passport_number')
    search_fields = ('first_name', 'last_name', 'email', 'passport_number')

    def booking_link(self, obj):
        url = reverse("admin:bookings_booking_change", args=[obj.booking.id])
        return format_html('<a href="{}">{}</a>', url, obj.booking)
    booking_link.short_description = 'Booking'

@admin.register(BookingAdditionalService)
class BookingAdditionalServiceAdmin(admin.ModelAdmin):
    list_display = ('service_name', 'booking_link', 'price')
    list_filter = ('service_name',)
    search_fields = ('service_name', 'booking__id')

    def booking_link(self, obj):
        url = reverse("admin:bookings_booking_change", args=[obj.booking.id])
        return format_html('<a href="{}">{}</a>', url, obj.booking)
    booking_link.short_description = 'Booking'

@admin.register(BookingExcursion)
class BookingExcursionAdmin(admin.ModelAdmin):
    list_display = ('excursion_name', 'booking_link')
    list_filter = ('cruise_excursion__excursion__name',)
    search_fields = ('cruise_excursion__excursion__name', 'booking__id')

    def booking_link(self, obj):
        url = reverse("admin:bookings_booking_change", args=[obj.booking.id])
        return format_html('<a href="{}">{}</a>', url, obj.booking)
    booking_link.short_description = 'Booking'

    def excursion_name(self, obj):
        return obj.cruise_excursion.excursion.name
    excursion_name.short_description = 'Excursion'