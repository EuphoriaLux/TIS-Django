# bookings/models.py
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from cruises.models import CruiseSession, CruiseCabinPrice, Cruise
from quote.models import Quote

class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        CANCELLED = 'cancelled', 'Cancelled'

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    quote = models.OneToOneField(Quote, on_delete=models.SET_NULL, null=True, blank=True)
    cruise_session = models.ForeignKey(CruiseSession, on_delete=models.CASCADE)
    cruise_cabin_price = models.ForeignKey(CruiseCabinPrice, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Booking {self.id} for {self.cruise_session.cruise.name}"

    def get_admin_url(self):
        return reverse('admin:bookings_booking_change', args=[self.id])

    @property
    def is_upcoming(self):
        return self.cruise_session.start_date > timezone.now().date()

    @property
    def passenger_count(self):
        return self.passengers.count()

class Passenger(models.Model):
    booking = models.ForeignKey(Booking, related_name='passengers', on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    date_of_birth = models.DateField()
    passport_number = models.CharField(max_length=50)
    passport_expiry_date = models.DateField()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class BookingAdditionalService(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='additional_services')
    service_name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.service_name} for Booking: {self.booking.id}"

class BookingExcursion(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='excursions')
    cruise_excursion = models.ForeignKey('cruises.CruiseExcursion', on_delete=models.CASCADE)
    passengers = models.ManyToManyField(Passenger, related_name='booked_excursions')

    def __str__(self):
        return f"Excursion {self.cruise_excursion.excursion.name} for Booking {self.booking.id}"