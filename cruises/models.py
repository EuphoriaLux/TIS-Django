# cruises/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Min, Q
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)  # Add soft delete capability

    class Meta:
        abstract = True

class Location(BaseModel):
    """Base model for any location (ports, cities, etc)"""
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    description = models.TextField(blank=True)
    timezone = models.CharField(max_length=50, blank=True)  # For handling arrival/departure times

    class Meta:
        unique_together = ['name', 'country']
        ordering = ['country', 'name']

    def __str__(self):
        return f"{self.name}, {self.country}"
    
class Port(Location):
    """Extends Location with port-specific attributes"""
    port_code = models.CharField(max_length=10, unique=True, blank=True)
    is_embarkation_port = models.BooleanField(default=False)
    is_disembarkation_port = models.BooleanField(default=False)
    max_ship_length = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Maximum ship length in meters"
    )
    has_customs = models.BooleanField(default=False)

class Company(BaseModel):
    """Base model for companies (cruise companies, tour operators, etc)"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField()
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)
    website = models.URLField(max_length=200, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        abstract = True
        ordering = ['name']

    def __str__(self):
        return self.name

class CruiseCompany(Company):
    fleet_size = models.PositiveIntegerField(default=0)
    operating_regions = models.ManyToManyField('Region', related_name='operating_companies')

    class Meta:
        verbose_name_plural = "Cruise Companies"

class Brand(Company):
    parent_company = models.ForeignKey(
        CruiseCompany, 
        on_delete=models.CASCADE, 
        related_name='brands',
        null=True,
        blank=True
    )
    featured = models.BooleanField(default=False)
    market_segment = models.CharField(
        max_length=20,
        choices=[
            ('luxury', _('Luxury')),
            ('premium', _('Premium')),
            ('contemporary', _('Contemporary')),
            ('expedition', _('Expedition'))
        ],
        default='contemporary'
    )

class Region(BaseModel):
    """Geographical regions for cruises"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    ports = models.ManyToManyField(Port, related_name='regions')
    parent_region = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='sub_regions'
    )

    def __str__(self):
        return self.name

class Ship(BaseModel):
    """Cruise ships"""
    name = models.CharField(max_length=100)
    company = models.ForeignKey(CruiseCompany, on_delete=models.CASCADE, related_name='ships')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='ships')
    year_built = models.PositiveIntegerField()
    passenger_capacity = models.PositiveIntegerField()
    crew_capacity = models.PositiveIntegerField()
    gross_tonnage = models.PositiveIntegerField()
    length = models.DecimalField(max_digits=6, decimal_places=2)
    speed = models.DecimalField(max_digits=4, decimal_places=1, help_text="Maximum speed in knots")
    
    class Meta:
        unique_together = ['name', 'company']
        ordering = ['company', 'name']

    def __str__(self):
        return f"{self.name} ({self.company.name})"

class CruiseType(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    typical_duration = models.PositiveIntegerField(help_text="Typical duration in days")
    requires_visa = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name

class Cruise(BaseModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField()
    cruise_type = models.ForeignKey(CruiseType, on_delete=models.CASCADE)
    ship = models.ForeignKey(Ship, on_delete=models.CASCADE, related_name='cruises')
    regions = models.ManyToManyField(Region, related_name='cruises')
    
    image = models.ImageField(upload_to='cruise_images/', null=True, blank=True)
    image_url = models.URLField(max_length=1000, null=True, blank=True)
    flyer_pdf = models.FileField(upload_to='cruise_flyers/', null=True, blank=True)
    
    is_featured = models.BooleanField(default=False)
    difficulty_level = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1 (Easy) to 5 (Challenging)",
        default=1
    )

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['cruise_type', 'is_featured']),
            models.Index(fields=['ship', 'is_active'])
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def company(self):
        return self.ship.company

    @property
    def brand(self):
        return self.ship.brand

    def get_min_price(self):
        """Get minimum price for this cruise from active sessions"""
        min_price = CruiseSessionCabinPrice.objects.filter(
            cruise_session__cruise=self,
            cruise_session__start_date__gte=timezone.now().date(),
            cruise_session__status__in=['booking', 'guaranteed'],
            available_cabins__gt=0
        ).aggregate(min_price=Min('price'))['min_price']
        return min_price

    @classmethod
    def get_featured_cruises(cls, count=3):
        """Get random featured cruises with available sessions and prices"""
        today = timezone.now().date()
        
        # Get cruises with active sessions
        active_cruises = cls.objects.filter(
            sessions__start_date__gte=today,
            sessions__status__in=['booking', 'guaranteed']
        ).distinct()
        
        # Get cruises with prices
        cruises_with_prices = []
        for cruise in active_cruises:
            min_price = cruise.get_min_price()
            if min_price is not None:
                cruise.min_price = min_price
                cruises_with_prices.append(cruise)
        
        # Randomly select featured cruises
        num_featured = min(count, len(cruises_with_prices))
        return random.sample(cruises_with_prices, num_featured) if cruises_with_prices else []

    @property
    def price_range(self):
        """Get price range across all available sessions"""
        prices = CruiseSessionCabinPrice.objects.filter(
            cruise_session__cruise=self,
            cruise_session__start_date__gte=timezone.now().date(),
            cruise_session__status__in=['booking', 'guaranteed'],
            available_cabins__gt=0
        )
        if not prices.exists():
            return None, None
        min_price = min(price.get_current_price() for price in prices)
        max_price = max(price.get_current_price() for price in prices)
        return min_price, max_price

    def get_cabin_availability(self, session=None):
        """Get cabin availability for specific or all sessions"""
        query = CruiseSessionCabinPrice.objects.filter(
            cruise_session__cruise=self,
            available_cabins__gt=0
        )
        if session:
            query = query.filter(cruise_session=session)
        
        return query.select_related(
            'cabin_category',
            'cruise_session'
        ).order_by(
            'cruise_session__start_date',
            'cabin_category__deck'
        )
    
    def get_upcoming_sessions(self):
        """Get all upcoming sessions ordered by start date"""
        return self.sessions.filter(
            start_date__gte=timezone.now().date(),
            status__in=['scheduled', 'booking', 'guaranteed']
        ).order_by('start_date')

    def get_active_sessions(self):
        """Get all active sessions (scheduled, booking, or guaranteed)"""
        return self.sessions.filter(
            status__in=['scheduled', 'booking', 'guaranteed']
        ).order_by('start_date')

    def get_next_session(self):
        """Get the next available session"""
        return self.get_upcoming_sessions().first()

    def get_session_count(self):
        """Get total number of sessions"""
        return self.sessions.count()

    def get_price_range(self):
        """Get price range across all available sessions"""
        prices = CruiseSessionCabinPrice.objects.filter(
            cruise_session__cruise=self,
            cruise_session__start_date__gte=timezone.now().date(),
            cruise_session__status__in=['booking', 'guaranteed'],
            available_cabins__gt=0
        )
        if not prices.exists():
            return None, None
        
        min_price = min(price.get_current_price() for price in prices)
        max_price = max(price.get_current_price() for price in prices)
        return min_price, max_price

    def get_available_cabin_categories(self):
        """Get all available cabin categories with at least one cabin available"""
        return CabinCategory.objects.filter(
            session_prices__cruise_session__cruise=self,
            session_prices__cruise_session__start_date__gte=timezone.now().date(),
            session_prices__cruise_session__status__in=['booking', 'guaranteed'],
            session_prices__available_cabins__gt=0
        ).distinct()

    def is_available(self):
        """Check if cruise has any available sessions"""
        return self.get_upcoming_sessions().exists()

    def has_session_in_date_range(self, start_date, end_date):
        """Check if cruise has any sessions in given date range"""
        return self.sessions.filter(
            start_date__lte=end_date,
            end_date__gte=start_date
        ).exists()

    @property
    def duration_range(self):
        """Get min and max duration of cruise sessions"""
        sessions = self.sessions.all()
        if not sessions.exists():
            return "No sessions scheduled"
            
        durations = [(session.end_date - session.start_date).days + 1 for session in sessions]
        min_duration = min(durations)
        max_duration = max(durations)
        
        if min_duration == max_duration:
            return f"{min_duration} days"
        return f"{min_duration}-{max_duration} days"

    def get_duration_display(self):
        """Format duration for admin display"""
        return self.duration_range
    get_duration_display.short_description = "Duration"

    @property
    def company(self):
        """Get cruise company through ship"""
        return self.ship.company

    @property
    def brand(self):
        """Get cruise brand through ship"""
        return self.ship.brand

class CruiseItinerary(BaseModel):
    """Model for cruise itineraries"""
    cruise = models.ForeignKey(
        Cruise,
        on_delete=models.CASCADE,
        related_name='itineraries'
    )
    day = models.PositiveIntegerField()
    port = models.ForeignKey(
        Port,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='itinerary_stops'
    )
    arrival_time = models.TimeField(null=True, blank=True)
    departure_time = models.TimeField(null=True, blank=True)
    description = models.TextField()
    is_sea_day = models.BooleanField(
        default=False,
        help_text=_("Indicate if this is a day at sea")
    )

    class Meta:
        ordering = ['cruise', 'day']
        unique_together = ['cruise', 'day']
        verbose_name_plural = _("Cruise Itineraries")
        indexes = [
            models.Index(fields=['cruise', 'day']),
            models.Index(fields=['port', 'arrival_time']),
        ]

    def __str__(self):
        if self.is_sea_day:
            return f"{self.cruise.name} - Day {self.day}: At Sea"
        return f"{self.cruise.name} - Day {self.day}: {self.port.name if self.port else 'TBD'}"

    @property
    def duration_at_port(self):
        """Calculate duration at port if both times are set"""
        if self.arrival_time and self.departure_time:
            from datetime import datetime, timedelta
            arrival = datetime.combine(datetime.today(), self.arrival_time)
            departure = datetime.combine(datetime.today(), self.departure_time)
            if departure < arrival:  # If departure is next day
                departure += timedelta(days=1)
            return departure - arrival
        return None

class CruiseSession(BaseModel):
    cruise = models.ForeignKey(Cruise, related_name='sessions', on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    embarkation_port = models.ForeignKey(
        Port, 
        on_delete=models.CASCADE,
        related_name='embarkation_sessions'
    )
    disembarkation_port = models.ForeignKey(
        Port,
        on_delete=models.CASCADE,
        related_name='disembarkation_sessions'
    )
    capacity = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('scheduled', _('Scheduled')),
            ('booking', _('Booking Open')),
            ('guaranteed', _('Guaranteed Departure')),
            ('fully_booked', _('Fully Booked')),
            ('completed', _('Completed')),
            ('cancelled', _('Cancelled'))
        ],
        default='scheduled'
    )
    promotion = models.ForeignKey(
        'Promotion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessions'
    )

    class Meta:
        unique_together = ('cruise', 'start_date')
        ordering = ['start_date']
        indexes = [
            models.Index(fields=['status', 'start_date'])
        ]

    @property
    def duration(self):
        """Calculate duration in days"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return None

    @property
    def duration_display(self):
        """Format duration for display"""
        days = self.duration
        if days:
            return f"{days} days"
        return "Duration not set"

    def __str__(self):
        return f"{self.cruise.name} ({self.start_date} to {self.end_date})"

    def get_price_range(self):
        """Get the min and max prices for this session"""
        prices = self.cabin_prices.all()
        if not prices:
            return None, None
        min_price = min(price.get_current_price() for price in prices)
        max_price = max(price.get_current_price() for price in prices)
        return min_price, max_price

    def get_available_cabin_categories(self):
        """Get all available cabin categories with prices"""
        return self.cabin_prices.filter(available_cabins__gt=0)

    def set_cabin_prices(self, category_prices):
        """
        Set prices for multiple cabin categories
        category_prices: dict of {cabin_category_id: price}
        """
        for category_id, price_data in category_prices.items():
            CruiseSessionCabinPrice.objects.update_or_create(
                cruise_session=self,
                cabin_category_id=category_id,
                defaults={
                    'price': price_data['price'],
                    'regular_price': price_data.get('regular_price', price_data['price']),
                    'is_early_bird': price_data.get('is_early_bird', False),
                    'early_bird_deadline': price_data.get('early_bird_deadline'),
                    'single_supplement': price_data.get('single_supplement', 50),
                    'third_person_discount': price_data.get('third_person_discount', 30),
                    'available_cabins': price_data.get('available_cabins', 0)
                }
            )

    def is_cabin_available(self, cabin_category, count=1):
        """Check if specific cabin category is available"""
        try:
            price = self.cabin_prices.get(cabin_category=cabin_category)
            return price.available_cabins >= count
        except CruiseSessionCabinPrice.DoesNotExist:
            return False

    def is_available(self):
        return self.status in ['booking', 'guaranteed']
    
    @property
    def min_price(self):
        """Get minimum price across all available sessions"""
        prices = CruiseSessionCabinPrice.objects.filter(
            cruise_session__cruise=self,
            cruise_session__start_date__gte=timezone.now().date(),
            cruise_session__status__in=['booking', 'guaranteed'],
            available_cabins__gt=0
        )
        if not prices.exists():
            return None
        return min(price.get_current_price() for price in prices)

    @property
    def price_range(self):
        """Get price range across all available sessions"""
        prices = CruiseSessionCabinPrice.objects.filter(
            cruise_session__cruise=self,
            cruise_session__start_date__gte=timezone.now().date(),
            cruise_session__status__in=['booking', 'guaranteed'],
            available_cabins__gt=0
        )
        if not prices.exists():
            return None, None
        min_price = min(price.get_current_price() for price in prices)
        max_price = max(price.get_current_price() for price in prices)
        return min_price, max_price

    def get_cabin_availability(self, session=None):
        """Get cabin availability for all or specific session"""
        query = CruiseSessionCabinPrice.objects.filter(
            cruise_session__cruise=self,
            available_cabins__gt=0
        )
        if session:
            query = query.filter(cruise_session=session)
        
        return query.select_related(
            'cabin_category',
            'cruise_session'
        ).order_by(
            'cruise_session__start_date',
            'cabin_category__deck'
        )

    def __str__(self):
        return f"{self.cruise.name} ({self.start_date} to {self.end_date})"

class Promotion(BaseModel):
    """New model for handling various types of promotions"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    promotion_type = models.CharField(
        max_length=50,
        choices=[
            ('early_bird', _('Early Bird')),
            ('last_minute', _('Last Minute')),
            ('seasonal', _('Seasonal Special')),
            ('group', _('Group Discount')),
            ('loyalty', _('Loyalty Reward'))
        ]
    )
    discount_type = models.CharField(
        max_length=20,
        choices=[
            ('percentage', _('Percentage')),
            ('fixed', _('Fixed Amount')),
            ('upgrade', _('Cabin Upgrade'))
        ]
    )
    discount_value = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    start_date = models.DateField()
    end_date = models.DateField()
    terms_conditions = models.TextField()

    def is_active(self):
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date

    def __str__(self):
        return f"{self.name} ({self.get_promotion_type_display()})"
    
class Excursion(BaseModel):
    """Base model for excursions"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    port = models.ForeignKey(
        Port,
        on_delete=models.CASCADE,
        related_name='excursions'
    )
    duration = models.DurationField(help_text=_("Duration in hours"))
    difficulty_level = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_("1 (Easy) to 5 (Challenging)"),
        default=1
    )
    minimum_participants = models.PositiveIntegerField(default=1)
    maximum_participants = models.PositiveIntegerField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    includes_transport = models.BooleanField(default=True)
    includes_meal = models.BooleanField(default=False)
    is_accessible = models.BooleanField(default=False)
    meeting_point = models.CharField(max_length=200)
    what_to_bring = models.TextField(blank=True)
    
    class Meta:
        ordering = ['port', 'name']
        indexes = [
            models.Index(fields=['port', 'name']),
            models.Index(fields=['difficulty_level', 'is_accessible']),
        ]

    def __str__(self):
        return f"{self.name} at {self.port.name}"

class CruiseExcursion(BaseModel):
    """Model linking excursions to specific cruise dates"""
    cruise = models.ForeignKey(
        Cruise,
        on_delete=models.CASCADE,
        related_name='excursions'
    )
    excursion = models.ForeignKey(
        Excursion,
        on_delete=models.PROTECT,
        related_name='cruise_excursions'
    )
    available_date = models.DateField()
    departure_time = models.TimeField()
    specific_meeting_point = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Override default meeting point if different")
    )
    available_spots = models.PositiveIntegerField()
    price_override = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=_("Override default excursion price if different")
    )

    class Meta:
        ordering = ['available_date', 'departure_time']
        unique_together = ['cruise', 'excursion', 'available_date', 'departure_time']
        indexes = [
            models.Index(fields=['cruise', 'available_date']),
            models.Index(fields=['available_spots']),
        ]

    @property
    def current_price(self):
        """Get the current price (override or default)"""
        return self.price_override if self.price_override is not None else self.excursion.price

    @property
    def meeting_location(self):
        """Get the meeting location (specific or default)"""
        return self.specific_meeting_point or self.excursion.meeting_point

    def is_available(self):
        """Check if the excursion is still available"""
        return (
            self.is_active and
            self.available_spots > 0 and
            self.available_date >= timezone.now().date()
        )

    def __str__(self):
        return f"{self.excursion.name} - {self.cruise.name} ({self.available_date})"
    
class Equipment(BaseModel):
    """Model for cabin and ship equipment/amenities"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    # Translations
    name_de = models.CharField(max_length=100, verbose_name=_("Name (German)"))
    name_fr = models.CharField(max_length=100, verbose_name=_("Name (French)"))
    description_de = models.TextField(verbose_name=_("Description (German)"))
    description_fr = models.TextField(verbose_name=_("Description (French)"))
    
    class Meta:
        verbose_name = _("Equipment")
        verbose_name_plural = _("Equipment")
        ordering = ['name']

    def __str__(self):
        return self.name
    
class CabinCategory(BaseModel):
    """Replaced CabinType with more specific CabinCategory"""
    name = models.CharField(max_length=100)
    ship = models.ForeignKey(Ship, on_delete=models.CASCADE, related_name='cabin_categories')
    description = models.TextField()
    capacity = models.PositiveIntegerField()
    deck = models.CharField(max_length=50)
    category_code = models.CharField(max_length=10)
    square_meters = models.DecimalField(max_digits=5, decimal_places=2)
    is_accessible = models.BooleanField(default=False)
    has_balcony = models.BooleanField(default=False)
    equipment = models.ManyToManyField('Equipment', through='CabinEquipment')

    class Meta:
        unique_together = ['ship', 'category_code']
        verbose_name_plural = "Cabin Categories"
        ordering = ['ship', 'deck', 'category_code']

    @classmethod
    def get_default_categories(cls):
        return [
            {
                'name': 'Emerald | 2-Bed Cabin',
                'description': 'Comfortable 16 m² cabin on the Emerald Deck.',
                'capacity': 2,
                'deck': 'Emerald',
                'category_code': 'EM2',
                'square_meters': Decimal('16.0'),
                'is_accessible': False,
                'has_balcony': False
            },
            {
                'name': 'Ruby | 2-Bed Cabin',
                'description': 'Luxurious 16 m² cabin on the Ruby Deck.',
                'capacity': 2,
                'deck': 'Ruby',
                'category_code': 'RB2',
                'square_meters': Decimal('16.0'),
                'is_accessible': False,
                'has_balcony': False
            }
            # ... add other categories
        ]

    def __str__(self):
        return f"{self.name} ({self.category_code}) - {self.ship.name}"

class CabinEquipment(BaseModel):
    """Through model for cabin category and equipment relationship"""
    cabin_category = models.ForeignKey(
        CabinCategory,
        on_delete=models.CASCADE,
        related_name='cabin_equipment'
    )
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='cabin_equipment'
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = _("Cabin Equipment")
        verbose_name_plural = _("Cabin Equipment")
        unique_together = ['cabin_category', 'equipment']
        ordering = ['cabin_category', 'equipment']

    def __str__(self):
        return f"{self.equipment.name} (x{self.quantity}) - {self.cabin_category.name}"
    
class CruiseSessionCabinPrice(BaseModel):
    """Model to manage cabin prices for specific cruise sessions"""
    cruise_session = models.ForeignKey(
        CruiseSession,
        on_delete=models.CASCADE,
        related_name='cabin_prices'
    )
    cabin_category = models.ForeignKey(
        CabinCategory,
        on_delete=models.PROTECT,
        related_name='session_prices'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    is_early_bird = models.BooleanField(default=False)
    early_bird_deadline = models.DateField(null=True, blank=True)
    regular_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_("Regular price after early bird deadline")
    )
    single_supplement = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=50,
        help_text=_("Single supplement percentage")
    )
    third_person_discount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=30,
        help_text=_("Third person discount percentage")
    )
    available_cabins = models.PositiveIntegerField(
        help_text=_("Number of cabins available in this category")
    )

    class Meta:
        verbose_name = _("Session Cabin Price")
        verbose_name_plural = _("Session Cabin Prices")
        unique_together = ['cruise_session', 'cabin_category']
        ordering = ['cruise_session', 'cabin_category']
        indexes = [
            models.Index(fields=['cruise_session', 'cabin_category']),
            models.Index(fields=['price']),
        ]

    def __str__(self):
        return f"{self.cabin_category.name} - {self.cruise_session} - €{self.price}"

    def get_current_price(self):
        """Get the current applicable price based on early bird status"""
        if self.is_early_bird and self.early_bird_deadline:
            if timezone.now().date() <= self.early_bird_deadline:
                return self.price
        return self.regular_price

    def get_single_price(self):
        """Calculate price for single occupation"""
        base_price = self.get_current_price()
        supplement = (base_price * self.single_supplement) / 100
        return base_price + supplement

    def get_third_person_price(self):
        """Calculate price for third person in cabin"""
        base_price = self.get_current_price()
        discount = (base_price * self.third_person_discount) / 100
        return base_price - discount

    @property
    def is_available(self):
        """Check if cabin category is still available"""
        return self.available_cabins > 0

    def decrease_availability(self, count=1):
        """Decrease available cabins"""
        if self.available_cabins >= count:
            self.available_cabins -= count
            self.save()
            return True
        return False