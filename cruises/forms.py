from django import forms
from .models import CruiseSession, CruiseCabinPrice


class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'class': 'form-control input-sm',
        'placeholder': 'Enter Name'
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control input-sm',
        'placeholder': 'Enter Email Address'
    }))
    mobile = forms.CharField(max_length=15, widget=forms.TextInput(attrs={
        'class': 'form-control input-sm',
        'placeholder': 'Enter Mobile Number'
    }))
    message = forms.CharField(widget=forms.Textarea(attrs={
        'class': 'form-control input-sm',
        'placeholder': 'Enter Your Message',
        'rows': 5
    }))