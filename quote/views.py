# quote/views.py

from django.http import FileResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_http_methods
from cruises.models import Cruise, CruiseSession, CruiseCategoryPrice
from .forms import BookingForm, QuoteForm, QuotePassengerForm, PassengerInfoForm, CruiseSelectionForm, ConfirmationForm
from .models import Booking, Quote, QuotePassenger
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

logger = logging.getLogger(__name__)

def quote_confirmation(request, quote_id):
    quote = get_object_or_404(Quote, id=quote_id)
    return render(request, 'quote/quote_confirmation.html', {'quote': quote})

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
    booking = get_object_or_404(Quote, id=booking_id)
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
            quote.user = request.user if not isinstance(request.user, AnonymousUser) else None
            quote.expiration_date = timezone.now() + datetime.timedelta(days=30)
            quote.save()
            
            QuotePassenger.objects.create(
                quote=quote,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
                phone=form.cleaned_data['phone']
            )
            
            return redirect('quote:quote_confirmation', quote_id=quote.id)
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
    return render(request, 'quote/booking_confirmation.html', {'booking': booking})



class CruiseBookingWizard(SessionWizardView):
    form_list = [PassengerInfoForm, CruiseSelectionForm, ConfirmationForm]
    template_name = "quote/book_cruise_wizard.html"

    def get_form(self, step=None, data=None, files=None):
        form = super().get_form(step, data, files)
        logger.info(f"Getting form for step: {step}")
        if step == '1':  # CruiseSelectionForm
            cruise_id = self.kwargs.get('cruise_id')
            if cruise_id:
                cruise = Cruise.objects.get(id=cruise_id)
                form.fields['cruise_session'].queryset = cruise.sessions.all()
                form.fields['cruise_category_price'].queryset = CruiseCategoryPrice.objects.filter(cruise=cruise)
        return form

    def process_step(self, form):
        logger.info(f"Processing step: {self.steps.current}")
        logger.info(f"Form data: {form.cleaned_data}")
        return self.get_form_step_data(form)

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        cruise_id = self.kwargs.get('cruise_id')
        context['cruise'] = get_object_or_404(Cruise, id=cruise_id)
        return context

    def done(self, form_list, **kwargs):
        try:
            logger.info("CruiseBookingWizard done method called")
            form_data = [form.cleaned_data for form in form_list]
            logger.info(f"Form data: {form_data}")

            passenger_info = form_data[0]
            cruise_selection = form_data[1]
            confirmation = form_data[2]

            quote = Quote.objects.create(
                user=self.request.user if self.request.user.is_authenticated else None,
                cruise_session=cruise_selection['cruise_session'],
                cruise_category_price=cruise_selection['cruise_category_price'],
                number_of_passengers=cruise_selection['number_of_passengers'],
                expiration_date=timezone.now() + datetime.timedelta(days=30),
                total_price=cruise_selection['cruise_category_price'].price * cruise_selection['number_of_passengers'],
                status='pending'
            )

            QuotePassenger.objects.create(
                quote=quote,
                first_name=passenger_info['first_name'],
                last_name=passenger_info['last_name'],
                email=passenger_info['email'],
                phone=passenger_info['phone']
            )

            logger.info(f"Quote created: {quote.id}")

            return redirect(reverse('quote:quote_confirmation', kwargs={'quote_id': quote.id}))
        except Exception as e:
            logger.error(f"Error in CruiseBookingWizard done method: {str(e)}")
            raise

    def render_revalidation_failure(self, failed_step, form):
        logger.error(f"Form revalidation failed at step: {failed_step}")
        return self.render(form)