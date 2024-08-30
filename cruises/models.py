from django.db import models
from django.contrib.auth.models import User
from django.core.validators import EmailValidator, MinValueValidator
from django.db.models import Min
from django.utils.text import slugify

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class CruiseCompany(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField()
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)
    website = models.URLField(max_length=200, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class CruiseType(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.name

class Brand(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField()
    logo = models.ImageField(upload_to='brand_logos/', null=True, blank=True)
    website = models.URLField(max_length=200, blank=True)
    featured = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Equipment(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.name

class CruiseCategory(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    equipment = models.ManyToManyField(Equipment, related_name='cruise_categories')

    def __str__(self):
        return self.name

class Cruise(BaseModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField()
    cruise_type = models.ForeignKey(CruiseType, on_delete=models.CASCADE)
    company = models.ForeignKey(CruiseCompany, on_delete=models.CASCADE)
    categories = models.ManyToManyField(CruiseCategory, through='CruiseCategoryPrice')
    image = models.ImageField(upload_to='cruise_images/', null=True, blank=True)
    image_url = models.URLField(max_length=1000, null=True, blank=True)
    flyer_pdf = models.FileField(upload_to='cruise_flyers/', null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def min_price(self):
        price = self.cruisecategoryprice_set.aggregate(Min('price'))['price__min']
        return price if price is not None else 'N/A'

    @property
    def duration(self):
        first_session = self.sessions.first()
        if first_session:
            return first_session.duration()
        return None

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

class CruiseCategoryPrice(BaseModel):
    cruise = models.ForeignKey(Cruise, on_delete=models.CASCADE)
    category = models.ForeignKey(CruiseCategory, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        unique_together = ('cruise', 'category')

    def __str__(self):
        return f"{self.cruise.name} - {self.category.name}: ${self.price}"

class CruiseSession(BaseModel):
    cruise = models.ForeignKey(Cruise, related_name='sessions', on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    capacity = models.PositiveIntegerField()

    class Meta:
        unique_together = ('cruise', 'start_date', 'end_date')

    def __str__(self):
        return f"{self.cruise.name} ({self.start_date} to {self.end_date})"

    def duration(self):
        return (self.end_date - self.start_date).days + 1