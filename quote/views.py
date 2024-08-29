# quote/views.py

from django import forms
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_http_methods
from cruises.models import Cruise, CruiseSession, CruiseCategoryPrice
from .forms import (
    BookingForm, QuoteForm, QuotePassengerForm, 
    PassengerInfoForm, CruiseSelectionForm, ConfirmationForm,
    PassengerCountForm, PassengerInfoFormSet
)
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

def quote_cruise(request, cruise_id):
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
            
            return redirect('quote:quote_confirmation')
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
    return render(request, 'quote/quote_cruise.html', context)

def booking_confirmation(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    return render(request, 'quote/booking_confirmation.html', {'booking': booking})


    form_list = [PassengerCountForm, formset_factory(PassengerInfoForm, extra=0), CruiseSelectionForm, ConfirmationForm]
    template_name = 'quote/book_cruise_wizard.html'
    
    def get_form(self, step=None, data=None, files=None):
        form = super().get_form(step, data, files)
        
        if step is None:
            step = self.steps.current
        
        logger.info(f"Getting form for step: {step}")
        
        if step == '1':
            step_0_data = self.storage.get_step_data('0')
            logger.info(f"Step 0 data: {step_0_data}")
            if step_0_data:
                passenger_count = int(step_0_data.get('0-passenger_count', 1))
                logger.info(f"Passenger count: {passenger_count}")
                PassengerInfoFormSet = formset_factory(PassengerInfoForm, extra=passenger_count)
                form = PassengerInfoFormSet(prefix='passenger', data=data, files=files)
                
                helper = FormHelper()
                helper.form_tag = False
                helper.layout = Layout(
                    Div(
                        HTML("<h4>Passenger {{ forloop.counter }}</h4>"),
                        Div('first_name', css_class='form-group col-md-6'),
                        Div('last_name', css_class='form-group col-md-6'),
                        Div('email', css_class='form-group col-md-6'),
                        Div('phone', css_class='form-group col-md-6'),
                        css_class='row passenger-form mb-4'
                    )
                )
                form.helper = helper
        else:
            form.helper = FormHelper()
            form.helper.form_tag = False
            if isinstance(form, forms.Form):
                form.helper.layout = Layout(*form.fields.keys(), Submit('next', 'Next', css_class='btn-primary'))
            else:
                form.helper.layout = Layout(Submit('next', 'Next', css_class='btn-primary'))
        
        logger.info(f"Form for step {step}: {form}")
        return form

    def process_step(self, form):
        logger.info(f"Processing step: {self.steps.current}")
        if self.steps.current == '0':
            # Save the passenger count
            cleaned_data = form.cleaned_data
            self.storage.set_step_data(self.steps.current, self.get_form_step_data(form))
            logger.info(f"Saved passenger count: {cleaned_data}")
        elif self.steps.current == '1':
            # Process formset data
            cleaned_data = []
            for f in form:
                if f.is_valid():
                    cleaned_data.append(f.cleaned_data)
                else:
                    logger.error(f"Form errors: {f.errors}")
                    raise ValidationError("Please correct the errors in the form.")
            logger.info(f"Processed passenger data: {cleaned_data}")
            return cleaned_data
        return self.get_form_step_data(form)

    def post(self, *args, **kwargs):
        logger.info("Post method called")
        try:
            wizard_goto_step = self.request.POST.get('wizard_goto_step', None)
            if wizard_goto_step and wizard_goto_step in self.get_form_list():
                return self.render_goto_step(wizard_goto_step)

            form = self.get_form(data=self.request.POST, files=self.request.FILES)
            if form.is_valid():
                logger.info("Form is valid")
                return self.render_next_step(form)
            else:
                logger.error(f"Form is invalid: {form.errors}")
                return self.render(form)
        except Exception as e:
            logger.exception(f"Error in post method: {str(e)}")
            return HttpResponseRedirect(self.request.path)

    def render_next_step(self, form):
        logger.info("Rendering next step")
        next_step = self.steps.next
        new_form = self.get_form(
            next_step,
            data=self.storage.get_step_data(next_step),
            files=self.storage.get_step_files(next_step),
        )
        logger.info(f"Next step: {next_step}, New form: {new_form}")
        return self.render(new_form)

    def done(self, form_list, **kwargs):
        logger.info("Done method called")
        try:
            passenger_count = int(self.get_cleaned_data_for_step('0')['passenger_count'])
            passenger_data = self.get_cleaned_data_for_step('1')
            cruise_selection = self.get_cleaned_data_for_step('2')
            
            # Create Quote object
            quote = Quote.objects.create(
                user=self.request.user if self.request.user.is_authenticated else None,
                cruise_session=cruise_selection['cruise_session'],
                cruise_category_price=cruise_selection['cruise_category_price'],
                number_of_passengers=passenger_count,
                total_price=cruise_selection['cruise_category_price'].price * passenger_count,
                status='pending',
                expiration_date=timezone.now() + datetime.timedelta(days=30)
            )
            
            # Create QuotePassenger objects
            for passenger in passenger_data:
                QuotePassenger.objects.create(
                    quote=quote,
                    first_name=passenger['first_name'],
                    last_name=passenger['last_name'],
                    email=passenger['email'],
                    phone=passenger['phone']
                )
            
            return redirect(reverse('quote:quote_confirmation'))
        except Exception as e:
            logger.exception(f"Error in done method: {str(e)}")
            return HttpResponseRedirect(reverse('quote:error_page'))

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        context['cruise'] = Cruise.objects.get(id=self.kwargs['cruise_id'])
        return context

    def render_revalidation_failure(self, failed_step, form):
        logger.error(f"Form revalidation failed at step: {failed_step}")
        return self.render(form)