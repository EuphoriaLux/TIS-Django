# cruises/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import EmailValidator
from django.db.models import Min

class CruiseCompany(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)
    website = models.URLField(max_length=200, blank=True)

    def __str__(self):
        return self.name

class CruiseType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name

class Brand(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    logo = models.ImageField(upload_to='brand_logos/', null=True, blank=True)
    website = models.URLField(max_length=200, blank=True)
    featured = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Equipment(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name

class CruiseCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    equipment = models.ManyToManyField(Equipment, related_name='cruise_categories')

    def __str__(self):
        return self.name

class Cruise(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    cruise_type = models.ForeignKey(CruiseType, on_delete=models.CASCADE)
    company = models.ForeignKey(CruiseCompany, on_delete=models.CASCADE)
    categories = models.ManyToManyField(CruiseCategory, through='CruiseCategoryPrice')
    image = models.ImageField(upload_to='cruise_images/', null=True, blank=True)
    image_url = models.URLField(max_length=1000, null=True, blank=True)
    flyer_pdf = models.FileField(upload_to='cruise_flyers/', null=True, blank=True)  # New field for PDF flyer

    def min_price(self):
        price = self.cruisecategoryprice_set.aggregate(Min('price'))['price__min']
        return price if price is not None else 'N/A'

    @classmethod
    def river_cruises(cls):
        return cls.objects.filter(cruise_type__name__icontains='river')

    @classmethod
    def maritime_cruises(cls):
        return cls.objects.exclude(cruise_type__name__icontains='river')

    def __str__(self):
        return self.name

    def get_image_url(self):
        if self.image:
            return self.image.url
        elif self.image_url:
            return self.image_url
        else:
            return "/api/placeholder/400/300"  # Default placeholder image

class CruiseCategoryPrice(models.Model):
    cruise = models.ForeignKey(Cruise, on_delete=models.CASCADE)
    category = models.ForeignKey(CruiseCategory, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.cruise.name} - {self.category.name}: ${self.price}"

class CruiseSession(models.Model):
    cruise = models.ForeignKey(Cruise, related_name='sessions', on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    capacity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.cruise.name} ({self.start_date} to {self.end_date})"

class Booking(models.Model):
    cruise_session = models.ForeignKey(CruiseSession, on_delete=models.CASCADE)
    cruise_category_price = models.ForeignKey(CruiseCategoryPrice, on_delete=models.SET_NULL,null=True,blank=True
)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(validators=[EmailValidator()])
    phone = models.CharField(max_length=20)
    number_of_passengers = models.PositiveIntegerField()
    booking_date = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], default='pending')

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.cruise_session.cruise.name}"

    def save(self, *args, **kwargs):
        if not self.total_price:
            self.total_price = self.cruise_category_price.price * self.number_of_passengers
        super().save(*args, **kwargs)