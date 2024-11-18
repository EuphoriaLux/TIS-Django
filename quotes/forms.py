# quote/forms.py

from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from cruises.models import (
    CruiseSession,
    CruiseSessionCabinPrice,
    CabinCategory
)
from .models import Quote, QuotePassenger

class QuoteForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=100, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=100, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        max_length=20, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    cruise_session = forms.ModelChoiceField(
        queryset=CruiseSession.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_("Cruise Session"),
    )

    cruise_session_cabin_price = forms.ModelChoiceField(
        queryset=CruiseSessionCabinPrice.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_("Cabin Category"),
    )

    number_of_passengers = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label=_("Number of Passengers"),
        help_text=_("Number of passengers sharing the cabin")
    )

    class Meta:
        model = Quote
        fields = [
            'cruise_session',
            'cruise_session_cabin_price',
            'number_of_passengers',
            'cancellation_policy'
        ]
        widgets = {
            'cancellation_policy': forms.Select(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        self.cruise = kwargs.pop('cruise', None)
        self.session = kwargs.pop('session', None)
        super().__init__(*args, **kwargs)

        if self.cruise:
            # Get available sessions
            self.fields['cruise_session'].queryset = CruiseSession.objects.filter(
                cruise=self.cruise,
                start_date__gte=timezone.now(),
                status__in=['booking', 'guaranteed']
            ).order_by('start_date')
            
            if self.session:
                self.fields['cruise_session'].initial = self.session

        if self.cruise and self.session:
            # Get available cabin prices for the session
            self.fields['cruise_session_cabin_price'].queryset = (
                CruiseSessionCabinPrice.objects.filter(
                    cruise_session=self.session,
                    is_active=True,
                    available_cabins__gt=0
                ).select_related('cabin_category')
            )
        
        self.fields['cruise_session_cabin_price'].label_from_instance = self.label_from_instance
        
        # Add CSS classes and any additional attributes
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-control'})

    def label_from_instance(self, obj):
        """Custom label for cabin price options"""
        current_price = obj.get_current_price()
        single_price = obj.get_single_price()
        third_price = obj.get_third_person_price()
        
        price_info = f"€{current_price:,.2f}"
        if obj.is_early_bird and obj.early_bird_deadline:
            price_info += f" (Early Bird until {obj.early_bird_deadline})"
        
        return f"{obj.cabin_category.name} - {price_info}"

    def clean(self):
        cleaned_data = super().clean()
        cruise_session_cabin_price = cleaned_data.get('cruise_session_cabin_price')
        number_of_passengers = cleaned_data.get('number_of_passengers')

        if cruise_session_cabin_price and number_of_passengers:
            # Check cabin capacity
            if number_of_passengers > cruise_session_cabin_price.cabin_category.capacity:
                raise ValidationError({
                    'number_of_passengers': _(
                        "Maximum %(capacity)d passengers allowed for %(cabin)s."
                    ) % {
                        'capacity': cruise_session_cabin_price.cabin_category.capacity,
                        'cabin': cruise_session_cabin_price.cabin_category.name
                    }
                })

            # Check availability
            if not cruise_session_cabin_price.available_cabins:
                raise ValidationError({
                    'cruise_session_cabin_price': _("This cabin category is no longer available.")
                })

            # Calculate prices
            base_price = cruise_session_cabin_price.get_current_price()
            if number_of_passengers == 1:
                base_price = cruise_session_cabin_price.get_single_price()
            elif number_of_passengers > 2:
                # For third person onwards, apply third person discount
                base_price = (
                    base_price * 2 +  # First two passengers at regular price
                    cruise_session_cabin_price.get_third_person_price() * (number_of_passengers - 2)
                ) / number_of_passengers

            cleaned_data['base_price'] = base_price
            cleaned_data['total_price'] = base_price * number_of_passengers

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set cabin category from the selected price
        if self.cleaned_data.get('cruise_session_cabin_price'):
            instance.cabin_category = self.cleaned_data['cruise_session_cabin_price'].cabin_category
            instance.base_price = self.cleaned_data['base_price']
            instance.total_price = self.cleaned_data['total_price']
        
        if commit:
            instance.save()
        
        return instance