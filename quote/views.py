# quote/views.py
from django import forms
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_http_methods
from cruises.models import Cruise, CruiseSession, CruiseCabinPrice
from .forms import QuoteForm
from .models import Quote, QuotePassenger
from django.contrib.auth.models import AnonymousUser
from .utils import generate_quote_pdf
from django.contrib import messages
from django.http import JsonResponse
import json
from django.utils import timezone
import datetime
from datetime import datetime, timedelta
from django.core.files.storage import DefaultStorage
from django.core.exceptions import ValidationError
from django.urls import reverse
import logging
from django.forms import formset_factory
from django.http import Http404
from django.db import transaction

from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path


logger = logging.getLogger(__name__)

@require_http_methods(["GET", "POST"])
def create_quote(request, cruise_id):
    if request.method == 'GET':
        # Handle fetching cabin prices based on session_id
        session_id = request.GET.get('session_id')
        if not session_id:
            return JsonResponse({'success': False, 'errors': 'No session_id provided'}, status=400)
        try:
            session = CruiseSession.objects.get(id=session_id, cruise_id=cruise_id)
            cabin_prices = CruiseCabinPrice.objects.filter(cruise_id=cruise_id, session=session).select_related('cabin_type')
            cabin_prices_data = [
                {
                    'id': cp.id,
                    'label': f"{cp.cabin_type.name}: €{cp.price}",
                } for cp in cabin_prices
            ]
            return JsonResponse({'success': True, 'cabin_prices': cabin_prices_data})
        except CruiseSession.DoesNotExist:
            return JsonResponse({'success': False, 'errors': 'Invalid session_id'}, status=400)
    
    elif request.method == 'POST':
        # Handle quote creation via AJAX
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'errors': 'Invalid JSON data'}, status=400)
        
        session_id = data.get('session_id')
        category_id = data.get('category_id')
        passenger_data = data.get('passenger', {})
        number_of_passengers = data.get('number_of_passengers', 1)
    
        try:
            # Fetch the cruise object
            cruise = get_object_or_404(Cruise, pk=cruise_id)
            
            # Initialize the form with provided data
            form = QuoteForm(data={
                'cruise_session': session_id,
                'cruise_cabin_price': category_id,
                'number_of_passengers': number_of_passengers,
                'first_name': passenger_data.get('first_name', ''),
                'last_name': passenger_data.get('last_name', ''),
                'email': passenger_data.get('email', ''),
                'phone': passenger_data.get('phone', ''),
            }, cruise=cruise)
            
            if form.is_valid():
                with transaction.atomic():
                    quote = form.save(commit=False)
                    quote.user = request.user if not isinstance(request.user, AnonymousUser) else None
                    quote.total_price = quote.cruise_cabin_price.price * quote.number_of_passengers
                    quote.expiration_date = timezone.now() + timedelta(days=30)
                    quote.save()
                    
                    # Create QuotePassenger
                    QuotePassenger.objects.create(
                        quote=quote,
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        email=form.cleaned_data['email'],
                        phone=form.cleaned_data['phone']
                    )
                    
                return JsonResponse({'success': True, 'quote_id': quote.id})
            else:
                # Return field-specific errors
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
        except (CruiseSession.DoesNotExist, CruiseCabinPrice.DoesNotExist):
            return JsonResponse({'success': False, 'errors': 'Invalid session or cabin type'}, status=400)
        except ValidationError as ve:
            return JsonResponse({'success': False, 'errors': ve.message_dict}, status=400)
        except Exception as e:
            logger.error(f"Error creating quote: {e}")
            return JsonResponse({'success': False, 'errors': 'An unexpected error occurred.'}, status=500)



def quote_cruise(request, cruise_id):
    cruise = get_object_or_404(Cruise, pk=cruise_id)
    selected_session_id = request.GET.get('session')
    selected_cabin_price_id = request.GET.get('cabin_price')

    logger.debug(f"Received quote_cruise request with session_id={selected_session_id} and cabin_price_id={selected_cabin_price_id}")

    selected_session = None
    selected_cabin_price = None

    if selected_session_id:
        try:
            selected_session = get_object_or_404(CruiseSession, pk=selected_session_id, cruise=cruise)
            logger.debug(f"Selected CruiseSession: {selected_session}")
        except Http404:
            logger.error(f"CruiseSession with id={selected_session_id} does not exist for Cruise id={cruise_id}")

    if selected_cabin_price_id and selected_session:
        try:
            selected_cabin_price = get_object_or_404(CruiseCabinPrice, pk=selected_cabin_price_id, cruise=cruise, session=selected_session)
            logger.debug(f"Selected CruiseCabinPrice: {selected_cabin_price}")
        except Http404:
            logger.error(f"CruiseCabinPrice with id={selected_cabin_price_id} does not exist for Cruise id={cruise_id} and Session id={selected_session_id}")

    initial_data = {
        'cruise_session': selected_session,
        'cruise_cabin_price': selected_cabin_price,
        'number_of_passengers': 1,
    }

    if request.method == 'POST':
        form = QuoteForm(request.POST, cruise=cruise, session=selected_session, initial=initial_data)
        if form.is_valid():
            try:
                with transaction.atomic():
                    quote = form.save(commit=False)
                    quote.cruise_session = form.cleaned_data['cruise_session']
                    quote.cruise_cabin_price = form.cleaned_data['cruise_cabin_price']
                    quote.total_price = quote.cruise_cabin_price.price * quote.number_of_passengers
                    quote.expiration_date = timezone.now() + timedelta(days=30)
                    quote.save()
                    
                    # Create QuotePassenger
                    QuotePassenger.objects.create(
                        quote=quote,
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        email=form.cleaned_data['email'],
                        phone=form.cleaned_data['phone']
                    )
                    
                messages.success(request, 'Your quote has been successfully created.')
                return redirect('quote:quote_confirmation')
            except Exception as e:
                logger.error(f"Error creating quote: {e}")
                messages.error(request, 'There was an error creating your quote. Please try again.')
    else:
        form = QuoteForm(cruise=cruise, session=selected_session, initial=initial_data)

    context = {
        'cruise': cruise,
        'form': form,
        'selected_session': selected_session,
        'selected_cabin_price': selected_cabin_price,
        'initial_total_price': selected_cabin_price.price if selected_cabin_price else 0,
    }

    logger.debug(f"Rendering quote_cruise.html with context: {context}")

    return render(request, 'quote/quote_cruise.html', context)

def quote_confirmation(request):
    return render(request, 'quote/quote_confirmation.html')

@staff_member_required
def convert_quote_to_booking(request, quote_id):
    quote = get_object_or_404(Quote, id=quote_id)
    if quote.can_convert_to_booking():
        try:
            booking = quote.convert_to_booking()
            messages.success(request, f"Quote {quote.id} successfully converted to Booking {booking.id}")
        except Exception as e:
            messages.error(request, f"Error converting Quote {quote.id} to Booking: {str(e)}")
    else:
        messages.warning(request, f"Quote {quote.id} cannot be converted to a booking.")
    return redirect('admin:quotes_quote_change', quote_id)

