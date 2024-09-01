# cruises/views.py
from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Cruise, CruiseSession, Brand, CruiseCabinPrice, CabinType,CruiseItinerary
from .forms import ContactForm
from django.conf import settings
from django.views.generic import ListView
from django.db.models import Min, OuterRef, Subquery, Prefetch
from django.utils import timezone
import random

def about(request):
    context = {
        'title': 'About Us',
        'description': 'Learn more about our company and our passion for cruises.',
        'team_members': [
            {
                'name': 'Rony Broun',
                'position': 'CEO & Chairman',
                'image': '/images/rony_broun_01s.jpg'
            },
            {
                'name': 'Rafaela Marques',
                'position': 'Portugal Office',
                'image': 'assets/images/team/place-holder.jpg'
            },
            {
                'name': 'Tom Scheuer',
                'position': 'Luxembourg Office',
                'image': 'assets/images/team/place-holder.jpg'
            },
            {
                'name': 'Patrick Lenaerts',
                'position': 'Belgium Office',
                'image': 'assets/images/team/place-holder.jpg'
            }
        ]
    }
        
    return render(request, 'about_us.html', context)

def home(request):
    # Subquery to get the minimum price for each cruise
    min_price_subquery = CruiseCabinPrice.objects.filter(
        cruise=OuterRef('pk')
    ).order_by('price').values('price')[:1]

    # Get all cruises with prices
    all_cruises = list(Cruise.objects.annotate(
        min_category_price=Subquery(min_price_subquery)
    ).filter(
        cruisecabinprice__isnull=False
    ).prefetch_related(
        Prefetch('sessions', 
                 queryset=CruiseSession.objects.filter(start_date__gte=timezone.now()).order_by('start_date'),
                 to_attr='future_sessions')
    ).distinct())

    # Randomly select 3 cruises
    featured_cruises = random.sample(all_cruises, min(3, len(all_cruises)))

    # Add next_session attribute to each featured cruise
    for cruise in featured_cruises:
        cruise.next_session = cruise.future_sessions[0] if cruise.future_sessions else None

    featured_brands = Brand.objects.filter(featured=True)

    context = {
        'featured_cruises': featured_cruises,
        'featured_brands': featured_brands,
    }

    return render(request, 'index.html', context)

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Here you can add logic to save the form data or send an email
            # For example:
            # name = form.cleaned_data['name']
            # email = form.cleaned_data['email']
            # mobile = form.cleaned_data['mobile']
            # message = form.cleaned_data['message']
            # Send email or save to database

            messages.success(request, 'Thank you for your message. We\'ll get back to you soon!')
            return redirect('contact')
    else:
        form = ContactForm()

    context = {
        'form': form,
        'title': 'Contact Us',
    }
    return render(request, 'contact_us.html', context)

def cruise_list(request):
    cruises = Cruise.objects.annotate(
        min_category_price=Subquery(
            CruiseCabinPrice.objects.filter(cruise=OuterRef('pk')).order_by('price').values('price')[:1]
        )
    ).filter(
        cruisecabinprice__isnull=False
    ).prefetch_related(
        Prefetch('sessions', 
                 queryset=CruiseSession.objects.filter(start_date__gte=timezone.now()).order_by('start_date'),
                 to_attr='future_sessions')
    ).distinct()
    
    for cruise in cruises:
        cruise.next_session = cruise.future_sessions[0] if cruise.future_sessions else None

    return render(request, 'cruises/cruise_list.html', {'cruises': cruises})

def cruise_detail(request, cruise_id):
    cruise = get_object_or_404(Cruise, pk=cruise_id)
    cabin_prices = CruiseCabinPrice.objects.filter(cruise=cruise).select_related('cabin_type', 'session')
        # Fetch the itinerary for the cruise
    itinerary = CruiseItinerary.objects.filter(cruise=cruise).order_by('day')

    context = {
        'cruise': cruise,
        'cabin_prices': cabin_prices,
        'has_summer_special': cruise.sessions.filter(is_summer_special=True).exists(),
        'itinerary': itinerary,  # Add the itinerary to the context
    }
    
    return render(request, 'cruises/cruise_detail.html', context)

def river_cruise_list(request):
    cruises = Cruise.river_cruises().annotate(
        min_category_price=Subquery(
            CruiseCabinPrice.objects.filter(cruise=OuterRef('pk')).order_by('price').values('price')[:1]
        )
    ).prefetch_related(
        Prefetch('sessions', 
                 queryset=CruiseSession.objects.filter(start_date__gte=timezone.now()).order_by('start_date'),
                 to_attr='future_sessions')
    ).distinct()
    
    for cruise in cruises:
        cruise.next_session = cruise.future_sessions[0] if cruise.future_sessions else None

    context = {
        'cruises': cruises,
        'cruise_type': 'River Cruises'
    }
    return render(request, 'cruises/cruise_list.html', context)

def maritime_cruise_list(request):
    cruises = Cruise.maritime_cruises().annotate(
        min_category_price=Subquery(
            CruiseCabinPrice.objects.filter(cruise=OuterRef('pk')).order_by('price').values('price')[:1]
        )
    ).prefetch_related(
        Prefetch('sessions', 
                 queryset=CruiseSession.objects.filter(start_date__gte=timezone.now()).order_by('start_date'),
                 to_attr='future_sessions')
    ).distinct()
    
    for cruise in cruises:
        cruise.next_session = cruise.future_sessions[0] if cruise.future_sessions else None

    context = {
        'cruises': cruises,
        'cruise_type': 'Maritime Cruises'
    }
    return render(request, 'cruises/cruise_list.html', context)

class FeaturedCruisesView(ListView):
    model = Cruise
    template_name = 'cruises/featured_cruises.html'
    context_object_name = 'featured_cruises'

    def get_queryset(self):
        cheapest_price = CabinType.objects.filter(
            cruise=OuterRef('pk')
        ).order_by('price').values('price')[:1]

        return Cruise.objects.annotate(
            min_category_price=Subquery(cheapest_price)
        ).filter(
            categories__isnull=False
        ).order_by('min_category_price')[:6]  # Limit to 6 featured cruises

def download_cruise_flyer(request, cruise_slug):
    cruise = get_object_or_404(Cruise, slug=cruise_slug)
    response = cruise.generate_pdf_flyer()
    if response:
        response['Content-Disposition'] = f'attachment; filename="{cruise.slug}_flyer.pdf"'
        return response
    return HttpResponse("Error generating PDF", status=500)