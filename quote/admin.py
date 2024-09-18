# quote/admin.py

from django.contrib import admin, messages
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from .models import Quote, QuotePassenger, QuoteAdditionalService
from .utils import generate_quote_pdf
from .views import convert_quote_to_booking


class QuotePassengerInline(admin.StackedInline):
    model = QuotePassenger
    extra = 0

@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ('passenger_display', 'cruise_session', 'total_price', 'status', 'created_at', 'booking_link', 'generate_quote_button')
    list_filter = ('status', 'created_at')
    search_fields = ('passengers__first_name', 'passengers__last_name', 'passengers__email', 'cruise_session__cruise__name')
    inlines = [QuotePassengerInline]

    def booking_link(self, obj):
        if hasattr(obj, 'booking'):
            url = reverse("admin:bookings_booking_change", args=[obj.booking.id])
            return format_html('<a href="{}">Booking {}</a>', url, obj.booking.id)
        return 'No Booking'
    booking_link.short_description = 'Booking'

    def passenger_display(self, obj):
        passenger = obj.passengers.first()
        if passenger:
            return f"{passenger.first_name} {passenger.last_name}"
        return "No passenger"
    passenger_display.short_description = 'Passenger'

    def generate_quote_button(self, obj):
        url = reverse('admin:generate_quote', args=[obj.pk])
        return format_html('<a class="button" href="{}">Create Quote</a>', url)
    generate_quote_button.short_description = 'Quote'

    def generate_quote_view(self, request, quote_id):
        quote = get_object_or_404(Quote, id=quote_id)
        pdf = generate_quote_pdf(quote)  # You'll need to update this function
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="quote_{quote.id}.pdf"'
        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('create-quote/<int:quote_id>/', self.admin_site.admin_view(self.generate_quote_view), name='generate_quote'),
            path('<int:quote_id>/convert/', self.admin_site.admin_view(convert_quote_to_booking), name='convert_quote_to_booking'),
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
                        f"Quote {quote.id} successfully converted to Booking {booking.id}",
                        messages.SUCCESS
                    )
                except Exception as e:
                    self.message_user(
                        request,
                        f"Error converting Quote {quote.id} to Booking: {str(e)}",
                        messages.ERROR
                    )
            else:
                self.message_user(
                    request,
                    f"Quote {quote.id} cannot be converted to a booking.",
                    messages.WARNING
                )
        
        if converted:
            self.message_user(request, f"{converted} quote(s) were converted to bookings.", messages.SUCCESS)
    convert_to_booking.short_description = "Convert selected quotes to bookings"

@admin.register(QuotePassenger)
class QuotePassengerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'quote')
    search_fields = ('first_name', 'last_name', 'email')

@admin.register(QuoteAdditionalService)
class QuoteAdditionalServiceAdmin(admin.ModelAdmin):
    list_display = ('service_name', 'quote', 'price')
    search_fields = ('service_name', 'quote__passengers__first_name', 'quote__passengers__last_name')
