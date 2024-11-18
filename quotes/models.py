# quotes/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, EmailValidator
from django.utils import timezone
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from cruises.models import (
    BaseModel,
    CruiseSession,
    CabinCategory,
    Ship,
    Promotion
)

class QuoteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'user',
            'cruise_session',
            'cruise_session__cruise',
            'cruise_session__cruise__ship',
            'cabin_category'
        )

    def get_active_quotes(self):
        return self.get_queryset().filter(
            status=Quote.Status.PENDING,
            expiration_date__gt=timezone.now()
        )

    def get_expired_quotes(self):
        return self.get_queryset().filter(
            status=Quote.Status.PENDING,
            expiration_date__lte=timezone.now()
        )

    def get_quotes_by_ship(self, ship_id):
        return self.get_queryset().filter(
            cruise_session__cruise__ship_id=ship_id
        )

class Quote(BaseModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        PENDING = 'pending', _('Pending')
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')
        EXPIRED = 'expired', _('Expired')
        CONVERTED = 'converted', _('Converted to Booking')

    class CancellationPolicy(models.TextChoices):
        FLEXIBLE = 'flexible', _('Flexible')
        MODERATE = 'moderate', _('Moderate')
        STRICT = 'strict', _('Strict')

    # Core relationships
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quotes'
    )
    cruise_session = models.ForeignKey(
        CruiseSession,
        on_delete=models.CASCADE,
        related_name='quotes'
    )
    cabin_category = models.ForeignKey(
        CabinCategory,
        on_delete=models.CASCADE,
        related_name='quotes'
    )
    
    # Pricing fields
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    number_of_passengers = models.PositiveIntegerField(
        default=2,
        validators=[MinValueValidator(1)]
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Applied promotions
    applied_promotion = models.ForeignKey(
        Promotion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quotes'
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Quote details
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    cancellation_policy = models.CharField(
        max_length=20,
        choices=CancellationPolicy.choices,
        default=CancellationPolicy.MODERATE
    )
    expiration_date = models.DateTimeField()
    note = models.TextField(blank=True)
    
    # Manager
    objects = QuoteManager()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'expiration_date']),
            models.Index(fields=['user', 'status']),
        ]

    def save(self, *args, **kwargs):
        if not self.expiration_date:
            # Set default expiration to 7 days from creation
            self.expiration_date = timezone.now() + timezone.timedelta(days=7)
        
        # Calculate total price
        self.calculate_total_price()
        super().save(*args, **kwargs)

    def calculate_total_price(self):
        """Calculate total price including base price, passengers, and discounts"""
        self.total_price = self.base_price * self.number_of_passengers
        
        if self.applied_promotion and self.applied_promotion.is_active():
            if self.applied_promotion.discount_type == 'percentage':
                discount = (self.total_price * self.applied_promotion.discount_value) / 100
            else:  # fixed amount
                discount = self.applied_promotion.discount_value
            self.discount_amount = discount
            self.total_price -= discount

    def can_convert_to_booking(self):
        return (
            not hasattr(self, 'booking') and  # No existing booking
            not self.is_expired() and  # Not expired
            self.status in [self.Status.PENDING, self.Status.APPROVED] and  # Valid status
            self.cruise_session.is_available() and  # Session is available
            self.cabin_category.ship == self.cruise_session.cruise.ship  # Valid cabin category
        )

    @transaction.atomic
    def convert_to_booking(self):
        if not self.can_convert_to_booking():
            raise ValueError(f"Quote {self.id} cannot be converted to a booking")

        # Import here to avoid circular import
        from bookings.models import Booking, Passenger as BookingPassenger

        # Create booking
        booking = Booking.objects.create(
            user=self.user,
            quote=self,
            cruise_session=self.cruise_session,
            cabin_category=self.cabin_category,
            number_of_passengers=self.number_of_passengers,
            total_price=self.total_price,
            applied_promotion=self.applied_promotion,
            discount_amount=self.discount_amount,
            status=Booking.Status.PENDING
        )

        # Copy passengers
        for quote_passenger in self.passengers.select_related():
            BookingPassenger.objects.create(
                booking=booking,
                **quote_passenger.get_passenger_data()
            )

        # Copy additional services
        for service in self.additional_services.all():
            booking.add_service(
                service_name=service.service_name,
                description=service.description,
                price=service.price
            )

        # Update quote status
        self.status = self.Status.CONVERTED
        self.save()

        return booking

    def is_expired(self):
        return self.expiration_date <= timezone.now()

    def mark_as_expired(self):
        if self.status == self.Status.PENDING:
            self.status = self.Status.EXPIRED
            self.save()

    def __str__(self):
        passenger = self.passengers.first()
        passenger_name = f"{passenger.first_name} {passenger.last_name}" if passenger else "No passenger"
        return f"Quote {self.id} - {passenger_name} - {self.cruise_session.cruise.name}"



class QuotePassenger(BaseModel):
    """Enhanced passenger model with more comprehensive information"""
    quote = models.ForeignKey(
        'Quote',
        related_name='passengers',
        on_delete=models.CASCADE
    )
    
    # Basic information
    first_name = models.CharField(_("First Name"), max_length=100)
    last_name = models.CharField(_("Last Name"), max_length=100)
    email = models.EmailField(_("Email"), validators=[EmailValidator()])
    phone = models.CharField(_("Phone"), max_length=20)
    date_of_birth = models.DateField(_("Date of Birth"), null=True, blank=True)
    
    # Optional information
    nationality = models.CharField(_("Nationality"), max_length=100, blank=True)
    passport_number = models.CharField(_("Passport Number"), max_length=50, blank=True)
    passport_expiry_date = models.DateField(_("Passport Expiry Date"), null=True, blank=True)
    dietary_requirements = models.TextField(_("Dietary Requirements"), blank=True)
    medical_requirements = models.TextField(_("Medical Requirements"), blank=True)
    
    # Lead passenger flag
    is_lead_passenger = models.BooleanField(
        _("Lead Passenger"),
        default=False,
        help_text=_("Designate this passenger as the lead contact for the quote")
    )
    
    class Meta:
        ordering = ['-is_lead_passenger', 'last_name', 'first_name']
        verbose_name = _("Quote Passenger")
        verbose_name_plural = _("Quote Passengers")
        indexes = [
            models.Index(fields=['quote', 'is_lead_passenger']),
            models.Index(fields=['passport_number']),
        ]

    def save(self, *args, **kwargs):
        # If this is the first passenger for the quote, make them the lead
        if not self.pk and not self.quote.passengers.exists():
            self.is_lead_passenger = True
        # Ensure only one lead passenger per quote
        elif self.is_lead_passenger:
            self.quote.passengers.exclude(pk=self.pk).update(is_lead_passenger=False)
        super().save(*args, **kwargs)

    def get_passenger_data(self):
        """Get passenger data for booking conversion"""
        return {
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'phone': self.phone,
            'date_of_birth': self.date_of_birth,
            'nationality': self.nationality,
            'passport_number': self.passport_number,
            'passport_expiry_date': self.passport_expiry_date,
            'dietary_requirements': self.dietary_requirements,
            'medical_requirements': self.medical_requirements,
            'is_lead_passenger': self.is_lead_passenger
        }

    @property
    def full_name(self):
        """Return the passenger's full name"""
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        lead_indicator = " (Lead)" if self.is_lead_passenger else ""
        return f"{self.full_name}{lead_indicator}"

class QuoteAdditionalService(BaseModel):
    """Enhanced additional services with more options and validation"""
    class ServiceType(models.TextChoices):
        TRANSFER = 'transfer', _('Transfer')
        EXCURSION = 'excursion', _('Excursion')
        INSURANCE = 'insurance', _('Insurance')
        BEVERAGE = 'beverage', _('Beverage Package')
        DINING = 'dining', _('Dining Package')
        OTHER = 'other', _('Other')

    quote = models.ForeignKey(
        Quote,
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
    
    class Meta:
        ordering = ['quote', 'service_type', 'service_name']

    @property
    def total_price(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.get_service_type_display()}: {self.service_name} for Quote {self.quote.id}"