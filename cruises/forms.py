from django import forms
from .models import Booking, CruiseSession, CruiseCategory

class BookingForm(forms.ModelForm):
    cruise_session = forms.ModelChoiceField(
        queryset=CruiseSession.objects.none(),
        empty_label="Select a cruise session",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    cruise_category = forms.ModelChoiceField(
        queryset=CruiseCategory.objects.none(),
        empty_label="Select a category",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Booking
        fields = ['cruise_session', 'cruise_category', 'first_name', 'last_name', 'email', 'phone', 'number_of_passengers']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'number_of_passengers': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        cruise = kwargs.pop('cruise', None)
        super().__init__(*args, **kwargs)
        
        if cruise:
            self.fields['cruise_session'].queryset = CruiseSession.objects.filter(cruise=cruise)
            self.fields['cruise_category'].queryset = CruiseCategory.objects.filter(cruise=cruise)

    def clean(self):
        cleaned_data = super().clean()
        cruise_session = cleaned_data.get('cruise_session')
        number_of_passengers = cleaned_data.get('number_of_passengers')

        if cruise_session and number_of_passengers:
            if number_of_passengers > cruise_session.capacity:
                raise forms.ValidationError("The number of passengers exceeds the available capacity for this cruise session.")

        return cleaned_data

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    subject = forms.CharField(max_length=200)
    message = forms.CharField(widget=forms.Textarea)