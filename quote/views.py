# views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import TravelPackage, Quote
from .forms import QuoteForm

@login_required
def create_quote(request):
    if request.method == 'POST':
        form = QuoteForm(request.POST)
        if form.is_valid():
            quote = form.save(commit=False)
            quote.customer = request.user.customer
            quote.save()
            # Send email with private quote
            return redirect('quote_sent')
    else:
        form = QuoteForm()
    return render(request, 'quote/create_quote.html', {'form': form})