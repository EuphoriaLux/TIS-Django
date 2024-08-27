# quotes/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from cruises.models import BaseModel, CruiseSession, CruiseCategoryPrice

class Quote(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quotes')
    cruise_session = models.ForeignKey(CruiseSession, on_delete=models.CASCADE)
    cruise_category_price = models.ForeignKey(CruiseCategoryPrice, on_delete=models.SET_NULL, null=True, blank=True)
    number_of_passengers = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    total_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired')
    ], default='pending')
    expiration_date = models.DateTimeField()
    
    def __str__(self):
        return f"Quote for {self.user.username} - {self.cruise_session.cruise.name}"

    def save(self, *args, **kwargs):
        if not self.total_price:
            self.total_price = self.cruise_category_price.price * self.number_of_passengers
        super().save(*args, **kwargs)

class QuotePassenger(BaseModel):
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name='passengers')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - Quote: {self.quote.id}"

class QuoteAdditionalService(BaseModel):
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name='additional_services')
    service_name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    def __str__(self):
        return f"{self.service_name} for Quote: {self.quote.id}"

class Booking(BaseModel):
    quote = models.OneToOneField(Quote, on_delete=models.SET_NULL, null=True, blank=True, related_name='booking')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    cruise_session = models.ForeignKey(CruiseSession, on_delete=models.CASCADE)
    cruise_category_price = models.ForeignKey(CruiseCategoryPrice, on_delete=models.SET_NULL, null=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=[
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], default='confirmed')
    
    def __str__(self):
        return f"Booking for {self.user.username} - {self.cruise_session.cruise.name}"

    def create_from_quote(quote):
        booking = Booking.objects.create(
            quote=quote,
            user=quote.user,
            cruise_session=quote.cruise_session,
            cruise_category_price=quote.cruise_category_price,
            total_price=quote.total_price,
            status='confirmed'
        )
        return booking