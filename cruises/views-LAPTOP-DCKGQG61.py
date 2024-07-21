# cruises/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Cruise, Booking, CruiseSession, CruiseCategory
from .forms import BookingForm, ContactForm
from django.conf import settings
import os


def about(request):
    context = {
        'title': 'About Us',
        'description': 'Learn more about our company and our passion for cruises.',
        'team_members': [
            {
                'name': 'John Doe',
                'position': 'CEO & Chairman',
                'image': '/images/rony_broun_01s.jpg'
            },
            {
                'name': 'Jane Smith',
                'position': 'COO',
                'image': 'assets/images/team/team-2.jpg'
            },
            {
                'name': 'Mike Johnson',
                'position': 'Head of Operations',
                'image': 'assets/images/team/team-3.jpg'
            }
        ]
    }
    
    template_path = os.path.join(settings.BASE_DIR, 'templates', 'about_us.html')
    print(f"Template path: {template_path}")
    print(f"Template exists: {os.path.exists(template_path)}")
    
    return render(request, 'about_us.html', context)

def home(request):
    featured_cruises = Cruise.objects.all()[:3]  # Get the first 3 cruises
    return render(request, 'home.html', {'featured_cruises': featured_cruises})

def index(request):
    featured_cruises = Cruise.objects.all()[:3]  # Get the first 3 cruises
    return render(request, 'new_index.html', {'featured_cruises': featured_cruises})

def packages(request):
    packages = [
        {
            'name': 'Amazon Cruise',
            'image': 'assets/images/packages/p1.jpg',
            'rating': 5,
            'price': 750,
            'description': 'Mattis interdum nunc massa. Velit. Nonummy penatibus',
            'features': ['fas fa-car', 'fab fa-fly', 'fas fa-cocktail', 'fas fa-umbrella-beach', 'far fa-bell']
        },
        # Add more packages as needed
    ]
    return render(request, 'packages.html', {'packages': packages})

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
    cruise = get_object_or_404(Cruise.objects.prefetch_related('categories', 'sessions'), pk=cruise_id)
    return render(request, 'cruises/cruise_detail.html', {'cruise': cruise})

def book_cruise(request, cruise_id):
    cruise = get_object_or_404(Cruise, pk=cruise_id)
    session_id = request.GET.get('session')
    category_id = request.GET.get('category')

    if not session_id or not category_id:
        messages.error(request, 'Please select both a cabin category and a cruise session.')
        return redirect('cruise_detail', cruise_id=cruise_id)

    initial_data = {
        'cruise_session': session_id,
        'cruise_category': category_id,
    }

    if request.method == 'POST':
        form = BookingForm(request.POST, cruise=cruise)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.total_price = booking.cruise_category.price * booking.number_of_passengers
            booking.save()
            messages.success(request, 'Your booking has been confirmed!')
            return redirect('booking_confirmation', booking_id=booking.id)
    else:
        form = BookingForm(cruise=cruise, initial=initial_data)

    selected_session = get_object_or_404(CruiseSession, pk=session_id)
    selected_category = get_object_or_404(CruiseCategory, pk=category_id)

    context = {
        'form': form,
        'cruise': cruise,
        'selected_session': selected_session,
        'selected_category': selected_category,
    }

    return render(request, 'cruises/book_cruise.html', context)

def booking_confirmation(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    return render(request, 'cruises/booking_confirmation.html', {'booking': booking})