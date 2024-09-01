# quote/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from .models import Quote, QuotePassenger, QuoteAdditionalService
from .utils import generate_quote_pdf


class QuotePassengerInline(admin.StackedInline):
    model = QuotePassenger
    extra = 0

@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ('passenger_display', 'cruise_session', 'total_price', 'status', 'created_at', 'generate_quote_button')
    list_filter = ('status', 'created_at')
    search_fields = ('passengers__first_name', 'passengers__last_name', 'passengers__email', 'cruise_session__cruise__name')
    inlines = [QuotePassengerInline]

    def passenger_display(self, obj):
        passenger = obj.passengers.first()
        if passenger:
            return f"{passenger.first_name} {passenger.last_name}"
        return "No passenger"
    passenger_display.short_description = 'Passenger'

    def generate_quote_button(self, obj):
        url = f'generate_quote/{obj.pk}/'
        return format_html('<a class="button" href="{}">Generate Quote</a>', url)
    generate_quote_button.short_description = 'Quote'
    generate_quote_button.allow_tags = True

    def generate_quote_view(self, request, quote_id):
        quote = get_object_or_404(Quote, id=quote_id)
        pdf = generate_quote_pdf(quote)  # You'll need to update this function
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="quote_{quote.id}.pdf"'
        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('generate_quote/<int:quote_id>/', self.admin_site.admin_view(self.generate_quote_view), name='generate_quote'),
        ]
        return custom_urls + urls

@admin.register(QuotePassenger)
class QuotePassengerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'quote')
    search_fields = ('first_name', 'last_name', 'email')

@admin.register(QuoteAdditionalService)
class QuoteAdditionalServiceAdmin(admin.ModelAdmin):
    list_display = ('service_name', 'quote', 'price')
    search_fields = ('service_name', 'quote__passengers__first_name', 'quote__passengers__last_name')
