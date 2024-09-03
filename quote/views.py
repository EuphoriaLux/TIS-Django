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
from django.core.files.storage import DefaultStorage
from django.core.exceptions import ValidationError
from django.urls import reverse
import logging
from django.forms import formset_factory
from django.http import Http404

logger = logging.getLogger(__name__)

@require_http_methods(["POST"])
def create_quote(request, cruise_id):
    data = json.loads(request.body)
    session_id = data.get('session_id')
    category_id = data.get('category_id')
    passenger_data = data.get('passenger', {})

    try:
        session = CruiseSession.objects.get(id=session_id, cruise_id=cruise_id)
        category_price = CruiseCabinPrice.objects.get(cruise_id=cruise_id, category_id=category_id)

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
    except (CruiseSession.DoesNotExist, CruiseCabinPrice.DoesNotExist):
        return JsonResponse({'success': False, 'errors': 'Invalid session or category'})
    except Exception as e:
        return JsonResponse({'success': False, 'errors': str(e)})

def quote_cruise(request, cruise_id):
    cruise = get_object_or_404(Cruise, pk=cruise_id)
    selected_session_id = request.GET.get('session')
    selected_cabin_price_id = request.GET.get('cabin_price')

    selected_session = None
    selected_cabin_price = None

    if selected_session_id:
        selected_session = get_object_or_404(CruiseSession, pk=selected_session_id, cruise=cruise)
    
    if selected_cabin_price_id and selected_session:
        selected_cabin_price = get_object_or_404(CruiseCabinPrice, pk=selected_cabin_price_id, cruise=cruise, session=selected_session)

    initial_data = {
        'cruise_session': selected_session,
        'cruise_cabin_price': selected_cabin_price,
        'number_of_passengers': 1,
    }

    if request.method == 'POST':
        form = QuoteForm(request.POST, cruise=cruise, session=selected_session, initial=initial_data)
        if form.is_valid():
            quote = form.save(commit=False)
            quote.cruise_session = form.cleaned_data['cruise_session']
            quote.cruise_cabin_price = form.cleaned_data['cruise_cabin_price']
            quote.total_price = quote.cruise_cabin_price.price * quote.number_of_passengers
            
            # Set the expiration date to 30 days from now (or any other duration you prefer)
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

            return redirect('quote:quote_confirmation')
    else:
        form = QuoteForm(cruise=cruise, session=selected_session, initial=initial_data)

    context = {
        'cruise': cruise,
        'form': form,
        'selected_session': selected_session,
        'selected_cabin_price': selected_cabin_price,
        'initial_total_price': selected_cabin_price.price if selected_cabin_price else 0,
    }

    return render(request, 'quote/quote_cruise.html', context)

def quote_confirmation(request):
    return render(request, 'quote/quote_confirmation.html')