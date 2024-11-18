# cruises/views.py
from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.views.generic import ListView
from django.db.models import Min, OuterRef, Subquery, Prefetch, Q
from django.utils import timezone
import random

from .models import (
    Cruise,
    CruiseSession,
    Brand,
    CruiseSessionCabinPrice,
    CabinCategory,
    CruiseItinerary
)
from .forms import ContactForm

def about(request):
    context = {
        'title': 'About Us',
        'description': 'Learn more about our company and our passion for cruises.',
        'team_members': [
            {
                'name': 'Rony Broun',
                'position': 'CEO & Chairman',
                'image': 'assets/images/rony_broun_01s.jpg'
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
    # Get current date
    today = timezone.now().date()

    # Get active cruise sessions with available cabins
    active_sessions = CruiseSession.objects.filter(
        start_date__gte=today,
        status__in=['booking', 'guaranteed']
    ).select_related('cruise', 'cruise__ship')

    # Get cruises with active sessions
    all_cruises = Cruise.objects.filter(
        sessions__in=active_sessions,
    ).prefetch_related(
        Prefetch(
            'sessions',
            queryset=active_sessions.order_by('start_date'),
            to_attr='available_sessions'
        )
    ).distinct()

    # Create a list to store cruises with their prices
    cruises_with_prices = []
    
    for cruise in all_cruises:
        # Get minimum price for this cruise from active sessions
        min_price = CruiseSessionCabinPrice.objects.filter(
            cruise_session__cruise=cruise,
            cruise_session__start_date__gte=today,
            cruise_session__status__in=['booking', 'guaranteed'],
            available_cabins__gt=0
        ).aggregate(min_price=Min('price'))['min_price']
        
        # Add price to cruise object
        cruise.min_price = min_price
        if min_price is not None:  # Only add cruises with available prices
            cruises_with_prices.append(cruise)
            # Add next session
            cruise.next_session = cruise.available_sessions[0] if cruise.available_sessions else None

    # Randomly select featured cruises from cruises that have prices
    num_featured = min(3, len(cruises_with_prices))
    featured_cruises = random.sample(cruises_with_prices, num_featured) if cruises_with_prices else []

    # Get featured brands
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
    active_sessions = CruiseSession.objects.filter(
        start_date__gte=timezone.now(),
        status__in=['booking', 'guaranteed']
    ).select_related('cruise', 'cruise__ship')

    min_price_subquery = CruiseSessionCabinPrice.objects.filter(
        cruise_session__cruise=OuterRef('pk'),
        cruise_session__in=active_sessions,
        available_cabins__gt=0
    ).order_by('price').values('price')[:1]

    cruises = Cruise.objects.filter(
        sessions__in=active_sessions
    ).annotate(
        min_price=Subquery(min_price_subquery)
    ).prefetch_related(
        Prefetch(
            'sessions',
            queryset=active_sessions.order_by('start_date'),
            to_attr='available_sessions'
        )
    ).distinct()

    for cruise in cruises:
        cruise.next_session = cruise.available_sessions[0] if cruise.available_sessions else None

    return render(request, 'cruises/cruise_list.html', {'cruises': cruises})

# cruises/views.py

def cruise_detail(request, cruise_id):
    cruise = get_object_or_404(Cruise, id=cruise_id)
    
    # Get all active sessions
    active_sessions = cruise.sessions.filter(
        start_date__gte=timezone.now().date(),
        status__in=['booking', 'guaranteed']
    ).order_by('start_date')

    # Get all cabin prices for active sessions
    session_prices = CruiseSessionCabinPrice.objects.filter(
        cruise_session__in=active_sessions,
        available_cabins__gt=0
    ).select_related(
        'cruise_session',
        'cabin_category'
    ).prefetch_related(
        'cabin_category__equipment'
    ).order_by(
        'cruise_session__start_date',
        'cabin_category__deck',
        'price'
    )

    # Check for summer special (you can customize this logic)
    has_summer_special = False
    today = timezone.now().date()
    if today.month in [6, 7, 8]:  # Summer months
        has_summer_special = True

    context = {
        'cruise': cruise,
        'active_sessions': active_sessions,
        'session_prices': session_prices,
        'has_summer_special': has_summer_special,
    }
    
    return render(request, 'cruises/cruise_detail.html', context)

def river_cruise_list(request):
    active_sessions = CruiseSession.objects.filter(
        start_date__gte=timezone.now(),
        status__in=['booking', 'guaranteed'],
        cruise__cruise_type__name__icontains='river'
    ).select_related('cruise', 'cruise__ship')

    min_price_subquery = CruiseSessionCabinPrice.objects.filter(
        cruise_session__cruise=OuterRef('pk'),
        cruise_session__in=active_sessions,
        available_cabins__gt=0
    ).order_by('price').values('price')[:1]

    cruises = Cruise.objects.filter(
        sessions__in=active_sessions
    ).annotate(
        min_price=Subquery(min_price_subquery)
    ).prefetch_related(
        Prefetch(
            'sessions',
            queryset=active_sessions.order_by('start_date'),
            to_attr='available_sessions'
        )
    ).distinct()

    for cruise in cruises:
        cruise.next_session = cruise.available_sessions[0] if cruise.available_sessions else None

    context = {
        'cruises': cruises,
        'cruise_type': 'River Cruises'
    }
    return render(request, 'cruises/cruise_list.html', context)

def maritime_cruise_list(request):
    active_sessions = CruiseSession.objects.filter(
        start_date__gte=timezone.now(),
        status__in=['booking', 'guaranteed']
    ).exclude(
        cruise__cruise_type__name__icontains='river'
    ).select_related('cruise', 'cruise__ship')

    min_price_subquery = CruiseSessionCabinPrice.objects.filter(
        cruise_session__cruise=OuterRef('pk'),
        cruise_session__in=active_sessions,
        available_cabins__gt=0
    ).order_by('price').values('price')[:1]

    cruises = Cruise.objects.filter(
        sessions__in=active_sessions
    ).annotate(
        min_price=Subquery(min_price_subquery)
    ).prefetch_related(
        Prefetch(
            'sessions',
            queryset=active_sessions.order_by('start_date'),
            to_attr='available_sessions'
        )
    ).distinct()

    for cruise in cruises:
        cruise.next_session = cruise.available_sessions[0] if cruise.available_sessions else None

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
        active_sessions = CruiseSession.objects.filter(
            start_date__gte=timezone.now(),
            status__in=['booking', 'guaranteed']
        )

        min_price_subquery = CruiseSessionCabinPrice.objects.filter(
            cruise_session__cruise=OuterRef('pk'),
            cruise_session__in=active_sessions,
            available_cabins__gt=0
        ).order_by('price').values('price')[:1]

        return Cruise.objects.filter(
            is_featured=True,
            sessions__in=active_sessions
        ).annotate(
            min_price=Subquery(min_price_subquery)
        ).prefetch_related(
            Prefetch(
                'sessions',
                queryset=active_sessions.order_by('start_date'),
                to_attr='available_sessions'
            )
        ).distinct()[:6]

def download_cruise_flyer(request, cruise_slug):
    cruise = get_object_or_404(Cruise, slug=cruise_slug)
    response = cruise.generate_pdf_flyer()
    if response:
        response['Content-Disposition'] = f'attachment; filename="{cruise.slug}_flyer.pdf"'
        return response
    return HttpResponse("Error generating PDF", status=500)