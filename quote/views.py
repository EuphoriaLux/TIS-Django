# quote/views.py

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from cruises.models import Booking
from .utils import generate_quote_pdf

def generate_quote(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    pdf = generate_quote_pdf(booking)
    return FileResponse(pdf, as_attachment=True, filename=f'quote_{booking.id}.pdf')