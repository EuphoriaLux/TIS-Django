# quotes/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from cruises.models import BaseModel, CruiseSession, CruiseCabinPrice
from django.utils import timezone
from django.db import transaction

class QuoteManager(models.Manager):
    def get_active_quotes(self):
        return self.filter(status=Quote.Status.PENDING, expiration_date__gt=timezone.now())

    def get_expired_quotes(self):
        return self.filter(status=Quote.Status.PENDING, expiration_date__lte=timezone.now())

class BookingManager(models.Manager):
    def get_active_bookings(self):
        return self.filter(is_active=True)

class Quote(BaseModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        EXPIRED = 'expired', 'Expired'

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    cruise_session = models.ForeignKey(CruiseSession, on_delete=models.CASCADE)
    cruise_cabin_price = models.ForeignKey(CruiseCabinPrice, on_delete=models.SET_NULL, null=True, blank=True)

    number_of_passengers = models.PositiveIntegerField(default=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    expiration_date = models.DateTimeField()

    objects = QuoteManager()

    def can_convert_to_booking(self):
        # Check if a booking already exists for this quote
        if hasattr(self, 'booking'):
            return False  # Booking already exists

        # Check if the quote is expired
        if self.is_expired():
            return False

        # Check if the quote status allows conversion
        if self.status not in [self.Status.PENDING, self.Status.APPROVED]:
            return False

        # Additional conditions can be added here
        return True

    def convert_to_booking(self):
        if not self.can_convert_to_booking():
            raise Exception(f"Quote {self.id} cannot be converted to a booking")

        # Import inside the method to avoid circular import
        from bookings.models import Booking, Passenger as BookingPassenger

        with transaction.atomic():
            # Create the booking
            booking = Booking.objects.create(
                user=self.user,
                quote=self,
                cruise_session=self.cruise_session,
                cruise_cabin_price=self.cruise_cabin_price,
                total_price=self.total_price,
                status=Booking.Status.PENDING,
                is_paid=False,
            )

            # Copy passengers from Quote to Booking
            for quote_passenger in self.passengers.all():
                BookingPassenger.objects.create(
                    booking=booking,
                    first_name=quote_passenger.first_name,
                    last_name=quote_passenger.last_name,
                    email=quote_passenger.email,
                    phone=quote_passenger.phone,
                    # You may need to collect or handle these fields properly
                    date_of_birth=timezone.now().date(),  # Placeholder
                    passport_number='UNKNOWN',            # Placeholder
                    passport_expiry_date=timezone.now().date(),  # Placeholder
                )

            # Update quote status
            self.status = self.Status.APPROVED
            self.save()

            return booking

    def __str__(self):
        passenger = self.passengers.first()
        passenger_name = f"{passenger.first_name} {passenger.last_name}" if passenger else "No passenger"
        return f"Quote {self.id} for {passenger_name} - {self.cruise_session.cruise.name}"
    
    def save(self, *args, **kwargs):
        if not self.total_price and self.cruise_cabin_price:
            self.total_price = self.cruise_cabin_price.price * self.number_of_passengers
        super().save(*args, **kwargs)

    def is_expired(self):
        return self.expiration_date <= timezone.now()

    def mark_as_expired(self):
        self.status = self.Status.EXPIRED
        self.save()
    

class QuotePassenger(models.Model):
    quote = models.ForeignKey(Quote, related_name='passengers', on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class QuoteAdditionalService(BaseModel):
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name='additional_services')
    service_name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    def __str__(self):
        return f"{self.service_name} for Quote: {self.quote.id}"