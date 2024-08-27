# quote/views.py

from django.http import FileResponse
from django.shortcuts import get_object_or_404, render, redirect
from cruises.models import Cruise, CruiseSession, CruiseCategoryPrice
from .forms import BookingForm, QuoteForm, QuotePassengerForm
from .models import Booking, Quote, QuotePassenger
from .utils import generate_quote_pdf
from django.contrib import messages

from django.http import JsonResponse


# quote/views.py
import json
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import AnonymousUser
from .models import Quote, QuotePassenger
from cruises.models import CruiseSession, CruiseCategoryPrice
from .forms import QuoteForm


@require_http_methods(["POST"])
def create_quote(request, cruise_id):
    data = json.loads(request.body)
    session_id = data.get('session_id')
    category_id = data.get('category_id')
    passenger_data = data.get('passenger', {})

    try:
        session = CruiseSession.objects.get(id=session_id, cruise_id=cruise_id)
        category_price = CruiseCategoryPrice.objects.get(cruise_id=cruise_id, category_id=category_id)

        quote = Quote.objects.create(
            user=request.user if not isinstance(request.user, AnonymousUser) else None,
            cruise_session=session,
            cruise_category_price=category_price,
            number_of_passengers=1,  # You might want to add this as a user input
            total_price=category_price.price,  # This should be calculated based on number of passengers
            status='pending'
        )

        # Create QuotePassenger
        QuotePassenger.objects.create(
            quote=quote,
            first_name=passenger_data.get('first_name', ''),
            last_name=passenger_data.get('last_name', ''),
            email=passenger_data.get('email', ''),
            phone=passenger_data.get('phone', '')
        )

        return JsonResponse({'success': True, 'quote_id': quote.id})
    except (CruiseSession.DoesNotExist, CruiseCategoryPrice.DoesNotExist):
        return JsonResponse({'success': False, 'errors': 'Invalid session or category'})
    except Exception as e:
        return JsonResponse({'success': False, 'errors': str(e)})

def generate_quote(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    pdf = generate_quote_pdf(booking)
    return FileResponse(pdf, as_attachment=True, filename=f'quote_{booking.id}.pdf')

def book_cruise(request, cruise_id):
    cruise = get_object_or_404(Cruise, id=cruise_id)
    session_id = request.GET.get('session')
    category_id = request.GET.get('category')

    if request.method == 'POST':
        form = QuoteForm(request.POST, cruise=cruise)
        if form.is_valid():
            quote = form.save(commit=False)
            quote.user = request.user if request.user.is_authenticated else None
            quote.save()
            
            QuotePassenger.objects.create(
                quote=quote,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
                phone=form.cleaned_data['phone']
            )
            
            return redirect('quote_confirmation', quote_id=quote.id)
    else:
        initial_data = {}
        if session_id:
            initial_data['cruise_session'] = session_id
        if category_id:
            initial_data['cruise_category_price'] = category_id
        form = QuoteForm(initial=initial_data, cruise=cruise)

    context = {
        'cruise': cruise,
        'form': form,
    }
    return render(request, 'cruises/book_cruise.html', context)

def booking_confirmation(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    return render(request, 'cruises/booking_confirmation.html', {'booking': booking})
