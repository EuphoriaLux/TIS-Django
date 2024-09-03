# quotes/forms.py
from django import forms
from cruises.models import CruiseSession, CruiseCabinPrice
from .models import Quote, QuotePassenger

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

    cruise_cabin_price = forms.ModelChoiceField(
        queryset=CruiseCabinPrice.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Cabin Type",
    )

    class Meta:
        model = Quote
        fields = ['cruise_session', 'cruise_cabin_price', 'number_of_passengers']

    def __init__(self, *args, **kwargs):
        self.cruise = kwargs.pop('cruise', None)
        self.session = kwargs.pop('session', None)
        super().__init__(*args, **kwargs)

        if self.cruise:
            self.fields['cruise_session'].queryset = CruiseSession.objects.filter(cruise=self.cruise)
            if self.session:
                self.fields['cruise_session'].initial = self.session

        if self.cruise and self.session:
            self.fields['cruise_cabin_price'].queryset = CruiseCabinPrice.objects.filter(
                cruise=self.cruise,
                session=self.session
            )
        
        self.fields['cruise_cabin_price'].label_from_instance = self.label_from_instance
        self.fields['cruise_session'].widget.attrs.update({'onchange': 'this.form.submit();'})
        self.fields['cruise_cabin_price'].widget.attrs.update({'class': 'form-control'})
        self.fields['number_of_passengers'].widget.attrs.update({'class': 'form-control'})

    def label_from_instance(self, obj):
        return f"{obj.cabin_type.name}: €{obj.price}"

    def clean(self):
        cleaned_data = super().clean()
        cruise_cabin_price = cleaned_data.get('cruise_cabin_price')
        number_of_passengers = cleaned_data.get('number_of_passengers')

        if cruise_cabin_price and number_of_passengers:
            cleaned_data['total_price'] = cruise_cabin_price.price * number_of_passengers

        return cleaned_data