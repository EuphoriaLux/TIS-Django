# quote/views.py
from django import forms
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_http_methods
from cruises.models import Cruise, CruiseSession, CruiseCabinPrice
from .forms import (
    QuoteForm, QuotePassengerForm, 
    PassengerInfoForm, CruiseSelectionForm, ConfirmationForm,
    PassengerCountForm, PassengerInfoFormSet
)
from .models import Quote, QuotePassenger
from django.contrib.auth.models import AnonymousUser
from .utils import generate_quote_pdf
from django.contrib import messages
from django.http import JsonResponse
import json
from django.utils import timezone
import datetime
from formtools.wizard.views import SessionWizardView
from django.core.files.storage import DefaultStorage
from django.core.exceptions import ValidationError
from django.urls import reverse
import logging
from django.forms import formset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Div, HTML

logger = logging.getLogger(__name__)

def quote_confirmation(request):
    return render(request, 'quote/quote_confirmation.html')

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

def generate_quote(request, booking_id):
    booking = get_object_or_404(Quote, id=booking_id)
    pdf = generate_quote_pdf(booking)
    return FileResponse(pdf, as_attachment=True, filename=f'quote_{booking.id}.pdf')

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from datetime import timedelta
from .forms import QuoteForm
from .models import Quote, QuotePassenger
from cruises.models import Cruise, CruiseSession, CruiseCabinPrice

def quote_cruise(request, cruise_id):
    cruise = get_object_or_404(Cruise, id=cruise_id)
    session_id = request.GET.get('session')
    cabin_id = request.GET.get('cabin')
    
    initial_data = {}
    selected_session = None
    selected_cabin_price = None
    
    if session_id:
        selected_session = get_object_or_404(CruiseSession, id=session_id, cruise=cruise)
        initial_data['cruise_session'] = selected_session.id
        
        if cabin_id:
            try:
                selected_cabin_price = CruiseCabinPrice.objects.get(id=cabin_id, cruise=cruise, session=selected_session)
            except CruiseCabinPrice.DoesNotExist:
                selected_cabin_price = CruiseCabinPrice.objects.filter(cruise=cruise, session=selected_session).first()
        else:
            selected_cabin_price = CruiseCabinPrice.objects.filter(cruise=cruise, session=selected_session).first()
        
        if selected_cabin_price:
            initial_data['cruise_cabin_price'] = selected_cabin_price.id

    if request.method == 'POST':
        form = QuoteForm(request.POST, cruise=cruise, session=selected_session, initial=initial_data)
        if form.is_valid():
            quote = form.save(commit=False)
            quote.user = request.user if not isinstance(request.user, AnonymousUser) else None
            quote.expiration_date = timezone.now() + timedelta(days=30)
            quote.save()
            
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
        'initial_total_price': form.get_initial_total_price(),
    }
    return render(request, 'quote/quote_cruise.html', context)