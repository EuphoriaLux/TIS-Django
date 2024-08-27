# quotes/forms.py
from django import forms
from cruises.models import CruiseSession, CruiseCategoryPrice
from .models import Quote, QuotePassenger, Booking

class QuoteForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ['cruise_session', 'cruise_category_price', 'number_of_passengers']

    # Add fields for passenger information
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20)

    def __init__(self, *args, **kwargs):
        cruise = kwargs.pop('cruise', None)
        super().__init__(*args, **kwargs)
        if cruise:
            self.fields['cruise_session'].queryset = cruise.sessions.all()
            self.fields['cruise_category_price'].queryset = CruiseCategoryPrice.objects.filter(cruise=cruise)

    def clean(self):
        cleaned_data = super().clean()
        cruise_session = cleaned_data.get('cruise_session')
        number_of_passengers = cleaned_data.get('number_of_passengers')

        if cruise_session and number_of_passengers:
            if number_of_passengers > cruise_session.capacity:
                raise forms.ValidationError("The number of passengers exceeds the available capacity for this cruise session.")

        return cleaned_data

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

class BookingForm(forms.ModelForm):

    class Meta:
        model = Booking
        fields = ['quote']
        widgets = {
            'quote': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['quote'].queryset = Quote.objects.filter(user=user, status='approved')

    def clean(self):
        cleaned_data = super().clean()
        quote = cleaned_data.get('quote')
        if quote and quote.status != 'approved':
            raise forms.ValidationError("You can only create a booking from an approved quote.")
        return cleaned_data
    
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column

class PassengerInfoForm(forms.Form):
    title = "Passenger Information"
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-0'),
                Column('last_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'email',
            'phone',
            Submit('next', 'Next Step', css_class='btn-primary')
        )

    def clean(self):
        cleaned_data = super().clean()
        for field in self.fields:
            if not cleaned_data.get(field):
                raise forms.ValidationError(f"{field.replace('_', ' ').capitalize()} is required.")
        return cleaned_data
    

class CruiseSelectionForm(forms.Form):
    title = "Cruise Selection"
    cruise_session = forms.ModelChoiceField(queryset=CruiseSession.objects.all(), required=True)
    cruise_category_price = forms.ModelChoiceField(queryset=CruiseCategoryPrice.objects.all(), required=True)
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