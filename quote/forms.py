# quotes/forms.py
from django import forms
from cruises.models import CruiseSession, CruiseCategoryPrice
from .models import Quote, QuotePassenger, Booking

class QuoteForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Quote
        fields = ['cruise_session', 'cruise_category_price', 'number_of_passengers', 'first_name', 'last_name', 'email', 'phone']
        widgets = {
            'cruise_session': forms.Select(attrs={'class': 'form-control'}),
            'cruise_category_price': forms.Select(attrs={'class': 'form-control'}),
            'number_of_passengers': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        cruise = kwargs.pop('cruise', None)
        super().__init__(*args, **kwargs)
        
        if cruise:
            self.fields['cruise_session'].queryset = CruiseSession.objects.filter(cruise=cruise)
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