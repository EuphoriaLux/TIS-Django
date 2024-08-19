# cruises/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Cruise, Booking, CruiseSession, CruiseCategory, Brand, CruiseCategoryPrice
from .forms import BookingForm
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
    min_price_subquery = CruiseCategoryPrice.objects.filter(
        cruise=OuterRef('pk')
    ).order_by('price').values('price')[:1]

    # Get all cruises with prices
    all_cruises = list(Cruise.objects.annotate(
        min_category_price=Subquery(min_price_subquery)
    ).filter(
        cruisecategoryprice__isnull=False
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
            messages.success(request, 'Thank you for your message. We\'ll get back to you soon!')
            return redirect('contact')
    else:
        form = ContactForm()

    context = {
        'form': form,
        'title': 'Contact Us',
    }
    return render(request, 'contact_us.html', context)  # Changed to contact_us.html to match your file structure

def cruise_list(request):
    cruises = Cruise.objects.all()
    return render(request, 'cruises/cruise_list.html', {'cruises': cruises})

def cruise_detail(request, cruise_id):
    cruise = get_object_or_404(
        Cruise.objects.prefetch_related(
            'cruisecategoryprice_set',
            'cruisecategoryprice_set__category',
            'sessions'
        ),
        pk=cruise_id
    )
    return render(request, 'cruises/cruise_detail.html', {'cruise': cruise})

def river_cruise_list(request):
    cruises = Cruise.river_cruises().annotate(
        min_category_price=Subquery(
            CruiseCategoryPrice.objects.filter(cruise=OuterRef('pk')).order_by('price').values('price')[:1]
        )
    ).prefetch_related(
        Prefetch('sessions', 
                 queryset=CruiseSession.objects.filter(start_date__gte=timezone.now()).order_by('start_date'),
                 to_attr='future_sessions')
    )
    
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
            CruiseCategoryPrice.objects.filter(cruise=OuterRef('pk')).order_by('price').values('price')[:1]
        )
    ).prefetch_related(
        Prefetch('sessions', 
                 queryset=CruiseSession.objects.filter(start_date__gte=timezone.now()).order_by('start_date'),
                 to_attr='future_sessions')
    )
    
    for cruise in cruises:
        cruise.next_session = cruise.future_sessions[0] if cruise.future_sessions else None

    context = {
        'cruises': cruises,
        'cruise_type': 'Maritime Cruises'
    }
    return render(request, 'cruises/cruise_list.html', context)

def book_cruise(request, cruise_id):
    cruise = get_object_or_404(Cruise, pk=cruise_id)
    session_id = request.GET.get('session')
    category_id = request.GET.get('category')

    if not session_id or not category_id:
        messages.error(request, 'Please select both a cabin category and a cruise session.')
        return redirect('cruise_detail', cruise_id=cruise_id)

    selected_session = get_object_or_404(CruiseSession, pk=session_id)
    selected_category_price = get_object_or_404(CruiseCategoryPrice, category__id=category_id, cruise=cruise)

    initial_data = {
        'cruise_session': selected_session.id,
        'cruise_category_price': selected_category_price.id,
    }

    if request.method == 'POST':
        form = BookingForm(request.POST, cruise=cruise)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.total_price = booking.cruise_category_price.price * booking.number_of_passengers
            booking.save()
            messages.success(request, 'Your booking has been confirmed!')
            return redirect('booking_confirmation', booking_id=booking.id)
    else:
        form = BookingForm(cruise=cruise, initial=initial_data)

    context = {
        'form': form,
        'cruise': cruise,
        'selected_session': selected_session,
        'selected_category_price': selected_category_price,
    }

    return render(request, 'cruises/book_cruise.html', context)

def booking_confirmation(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    return render(request, 'cruises/booking_confirmation.html', {'booking': booking})

class FeaturedCruisesView(ListView):
    model = Cruise
    template_name = 'cruises/featured_cruises.html'
    context_object_name = 'featured_cruises'

    def get_queryset(self):
        cheapest_price = CruiseCategory.objects.filter(
            cruise=OuterRef('pk')
        ).order_by('price').values('price')[:1]

        return Cruise.objects.annotate(
            min_category_price=Subquery(cheapest_price)
        ).filter(
            categories__isnull=False
        ).order_by('min_category_price')[:6]  # Limit to 6 featured cruises

