# quotes/forms.py
from django import forms
from cruises.models import CruiseSession, CruiseCabinPrice
from .models import Quote, QuotePassenger
from django.forms import formset_factory

class QuoteForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20)


    cruise_session = forms.ModelChoiceField(
        queryset=CruiseSession.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Cruise Session",
    )


    class Meta:
        model = Quote
        fields = ['cruise_session', 'cruise_cabin_price', 'number_of_passengers']

    def __init__(self, *args, **kwargs):
        self.cruise = kwargs.pop('cruise', None)
        self.selected_session = kwargs.pop('session', None)
        super().__init__(*args, **kwargs)

        if self.cruise:
            self.fields['cruise_session'].queryset = CruiseSession.objects.filter(cruise=self.cruise)
            self.fields['cruise_session'].label_from_instance = self.label_from_instance

            if self.selected_session:
                self.fields['cruise_cabin_price'].queryset = CruiseCabinPrice.objects.filter(
                    cruise=self.cruise,
                    session=self.selected_session
                )
            else:
                self.fields['cruise_cabin_price'].queryset = CruiseCabinPrice.objects.none()

        self.fields['cruise_session'].widget.attrs.update({'onchange': 'this.form.submit();'})
        self.fields['cruise_cabin_price'].widget.attrs.update({'class': 'form-control'})
        self.fields['number_of_passengers'].widget.attrs.update({'class': 'form-control'})


    def label_from_instance(self, obj):
        """Override the label for each option in the cruise_session dropdown."""
        return f"{obj.start_date.strftime('%b %d, %Y')} - {obj.end_date.strftime('%b %d, %Y')}"

    def clean(self):
        cleaned_data = super().clean()
        cruise_cabin_price = cleaned_data.get('cruise_cabin_price')
        number_of_passengers = cleaned_data.get('number_of_passengers')

        if cruise_cabin_price and number_of_passengers:
            cleaned_data['total_price'] = cruise_cabin_price.price * number_of_passengers

        return cleaned_data

    def get_initial_cabin_price(self):
        if self.initial.get('cruise_cabin_price'):
            return CruiseCabinPrice.objects.get(id=self.initial['cruise_cabin_price'])
        return None

    def get_initial_total_price(self):
        initial_cabin_price = self.get_initial_cabin_price()
        initial_passengers = self.initial.get('number_of_passengers', 1)
        if initial_cabin_price:
            return initial_cabin_price.price * initial_passengers
        return 0

class QuotePassengerForm(forms.ModelForm):
    class Meta:
        model = QuotePassenger
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column


class PassengerCountForm(forms.Form):
    title = "Number of Passengers"
    passenger_count = forms.ChoiceField(
        choices=[(i, str(i)) for i in range(1, 5)],
        label="How many passengers?",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'passenger_count',
            Submit('next', 'Next', css_class='btn-primary')
        )

class PassengerInfoForm(forms.Form):
    title = "Passenger Information"
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-0'),
                Column('last_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('email', css_class='form-group col-md-6 mb-0'),
                Column('phone', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            )
        )

PassengerInfoFormSet = formset_factory(PassengerInfoForm, extra=0)
    
class CruiseSelectionForm(forms.Form):
    title = "Cruise Selection"
    cruise_session = forms.ModelChoiceField(queryset=CruiseSession.objects.all(), required=True)
    cruise_category_price = forms.ModelChoiceField(queryset=CruiseCabinPrice.objects.all(), required=True)
    number_of_passengers = forms.IntegerField(min_value=1, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'cruise_session',
            'cruise_category_price',
            'number_of_passengers',
            Submit('next', 'Next Step', css_class='btn-primary')
        )

    def clean(self):
        cleaned_data = super().clean()
        for field in self.fields:
            if not cleaned_data.get(field):
                raise forms.ValidationError(f"{field.replace('_', ' ').capitalize()} is required.")
        
        cruise_session = cleaned_data.get('cruise_session')
        number_of_passengers = cleaned_data.get('number_of_passengers')
        if cruise_session and number_of_passengers:
            if number_of_passengers > cruise_session.capacity:
                raise forms.ValidationError("The number of passengers exceeds the available capacity for this cruise session.")
        return cleaned_data

class ConfirmationForm(forms.Form):
    title = "Confirmation"
    terms_accepted = forms.BooleanField(required=True, label="I accept the terms and conditions")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'terms_accepted',
            Submit('submit', 'Complete Booking', css_class='btn-success')
        )

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('terms_accepted'):
            raise forms.ValidationError("You must accept the terms to proceed.")
        return cleaned_data