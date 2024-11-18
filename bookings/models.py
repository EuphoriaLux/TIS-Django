# bookings/models.py
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, EmailValidator
from decimal import Decimal

from cruises.models import (
    BaseModel,
    CruiseSession,
    CabinCategory,
    Ship,
    Promotion,
    CruiseExcursion
)

class BookingManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'user',
            'quote',
            'cruise_session',
            'cruise_session__cruise',
            'cruise_session__cruise__ship',
            'cabin_category'
        )

    def get_active_bookings(self):
        return self.get_queryset().filter(
            status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED]
        )

    def get_upcoming_bookings(self):
        return self.get_active_bookings().filter(
            cruise_session__start_date__gt=timezone.now().date()
        )

    def get_bookings_by_ship(self, ship_id):
        return self.get_queryset().filter(
            cruise_session__cruise__ship_id=ship_id
        )

class Booking(BaseModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        PENDING = 'pending', _('Pending')
        CONFIRMED = 'confirmed', _('Confirmed')
        CANCELLED = 'cancelled', _('Cancelled')
        COMPLETED = 'completed', _('Completed')
        REFUNDED = 'refunded', _('Refunded')

    class PaymentStatus(models.TextChoices):
        UNPAID = 'unpaid', _('Unpaid')
        PARTIALLY_PAID = 'partially_paid', _('Partially Paid')
        PAID = 'paid', _('Fully Paid')
        REFUNDED = 'refunded', _('Refunded')

    # Core relationships
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings'
    )
    quote = models.OneToOneField(
        'quotes.Quote',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='booking'
    )
    cruise_session = models.ForeignKey(
        CruiseSession,
        on_delete=models.PROTECT,  # Prevent deletion of sessions with bookings
        related_name='bookings'
    )
    cabin_category = models.ForeignKey(
        CabinCategory,
        on_delete=models.PROTECT,
        related_name='bookings'
    )

    # Status and payment fields
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID
    )

    # Pricing fields
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)]
    )

    # Promotion fields
    applied_promotion = models.ForeignKey(
        Promotion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings'
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)]
    )

    # Additional fields
    special_requests = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    confirmation_number = models.CharField(max_length=50, unique=True, null=True, blank=True)

    objects = BookingManager()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'payment_status']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['cruise_session', 'cabin_category']),
        ]

    def __str__(self):
        lead_passenger = self.passengers.first()
        passenger_name = lead_passenger.full_name if lead_passenger else "No passenger"
        return f"Booking {self.confirmation_number} - {passenger_name}"

    def save(self, *args, **kwargs):
        if not self.confirmation_number and self.status == self.Status.CONFIRMED:
            self.confirmation_number = self.generate_confirmation_number()
        super().save(*args, **kwargs)

    def get_admin_url(self):
        return reverse('admin:bookings_booking_change', args=[self.id])

    @property
    def is_upcoming(self):
        return self.cruise_session.start_date > timezone.now().date()

    @property
    def passenger_count(self):
        return self.passengers.count()

    @property
    def balance_due(self):
        return self.total_price - self.amount_paid

    def calculate_total_price(self):
        """Calculate total price including additional services and excursions"""
        base_total = self.base_price
        
        # Add additional services
        service_total = sum(service.total_price for service in self.additional_services.all())
        
        # Add excursion costs
        excursion_total = sum(booking.total_price for booking in self.excursion_bookings.all())
        
        # Apply promotion discount if applicable
        if self.applied_promotion and self.applied_promotion.is_active():
            if self.applied_promotion.discount_type == 'percentage':
                self.discount_amount = (base_total * self.applied_promotion.discount_value) / 100
            else:  # fixed amount
                self.discount_amount = self.applied_promotion.discount_value
        
        self.total_price = base_total + service_total + excursion_total - self.discount_amount
        self.save()

    def generate_confirmation_number(self):
        """Generate a unique confirmation number"""
        import uuid
        return f"BK{timezone.now().year}{uuid.uuid4().hex[:6].upper()}"

    def cancel(self, reason=''):
        """Cancel the booking"""
        if self.status not in [self.Status.PENDING, self.Status.CONFIRMED]:
            raise ValueError("Cannot cancel booking with current status")
        
        self.status = self.Status.CANCELLED
        self.cancellation_reason = reason
        self.save()

    def record_payment(self, amount):
        """Record a payment for the booking"""
        if amount <= 0:
            raise ValueError("Payment amount must be positive")
        
        self.amount_paid += Decimal(str(amount))
        
        if self.amount_paid >= self.total_price:
            self.payment_status = self.PaymentStatus.PAID
        elif self.amount_paid > 0:
            self.payment_status = self.PaymentStatus.PARTIALLY_PAID
            
        self.save()

class Passenger(BaseModel):
    """Enhanced passenger model with more comprehensive information"""
    booking = models.ForeignKey(
        Booking,
        related_name='passengers',
        on_delete=models.CASCADE
    )
    
    # Basic information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(validators=[EmailValidator()])
    phone = models.CharField(max_length=20)
    date_of_birth = models.DateField()
    
    # Travel documents
    nationality = models.CharField(max_length=100)
    passport_number = models.CharField(max_length=50)
    passport_expiry_date = models.DateField()
    passport_issued_country = models.CharField(max_length=100)
    
    # Additional information
    dietary_requirements = models.TextField(blank=True)
    medical_requirements = models.TextField(blank=True)
    is_lead_passenger = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-is_lead_passenger', 'last_name', 'first_name']
        indexes = [
            models.Index(fields=['booking', 'is_lead_passenger']),
            models.Index(fields=['passport_number']),
        ]

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age_at_departure(self):
        if self.date_of_birth and self.booking.cruise_session.start_date:
            departure_date = self.booking.cruise_session.start_date
            age = departure_date.year - self.date_of_birth.year
            # Adjust age if birthday hasn't occurred this year
            if departure_date.month < self.date_of_birth.month or \
               (departure_date.month == self.date_of_birth.month and 
                departure_date.day < self.date_of_birth.day):
                age -= 1
            return age
        return None

    def __str__(self):
        return f"{self.full_name} ({'Lead' if self.is_lead_passenger else 'Guest'})"

class BookingAdditionalService(BaseModel):
    """Enhanced additional services with more options"""
    class ServiceType(models.TextChoices):
        TRANSFER = 'transfer', _('Transfer')
        INSURANCE = 'insurance', _('Insurance')
        BEVERAGE = 'beverage', _('Beverage Package')
        DINING = 'dining', _('Dining Package')
        INTERNET = 'internet', _('Internet Package')
        SPA = 'spa', _('Spa Package')
        OTHER = 'other', _('Other')

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='additional_services'
    )
    service_type = models.CharField(
        max_length=20,
        choices=ServiceType.choices,
        default=ServiceType.OTHER
    )
    service_name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    quantity = models.PositiveIntegerField(default=1)
    is_per_person = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['booking', 'service_type', 'service_name']

    @property
    def total_price(self):
        base_price = self.price * self.quantity
        if self.is_per_person:
            return base_price * self.booking.passenger_count
        return base_price

    def __str__(self):
        return f"{self.get_service_type_display()}: {self.service_name}"


class ExcursionBooking(BaseModel):
    """Enhanced excursion booking model"""
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='excursion_bookings'
    )
    cruise_excursion = models.ForeignKey(  # Changed from excursion to cruise_excursion
        CruiseExcursion,
        on_delete=models.PROTECT,
        related_name='bookings'
    )
    passengers = models.ManyToManyField(
        'Passenger',  # Using string reference to avoid circular import
        related_name='booked_excursions'
    )
    special_requirements = models.TextField(blank=True)
    pickup_location = models.CharField(max_length=200, blank=True)
    
    class Meta:
        ordering = ['booking', 'cruise_excursion']
        unique_together = ['booking', 'cruise_excursion']

    @property
    def total_price(self):
        return self.cruise_excursion.excursion.price * self.passengers.count()

    def __str__(self):
        return f"{self.cruise_excursion.excursion.name} - {self.passengers.count()} passengers"