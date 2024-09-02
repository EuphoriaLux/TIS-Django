from django.db import models
from django.contrib.auth.models import User
from django.core.validators import EmailValidator, MinValueValidator
from django.db.models import Min
from django.utils.text import slugify
from django.template.loader import get_template
from io import BytesIO
from django.http import HttpResponse
from xhtml2pdf import pisa
from django.conf import settings
import base64
import os
import logging
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)

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

    class Meta:
        verbose_name_plural = "Cruise Companies"

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
    name_de = models.CharField(max_length=100)
    name_fr = models.CharField(max_length=100)
    description_de = models.TextField()
    description_fr = models.TextField()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Equipment"

class Cruise(BaseModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField()
    cruise_type = models.ForeignKey(CruiseType, on_delete=models.CASCADE)
    company = models.ForeignKey(CruiseCompany, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True)

    image = models.ImageField(upload_to='cruise_images/', null=True, blank=True)
    image_url = models.URLField(max_length=1000, null=True, blank=True)
    flyer_pdf = models.FileField(upload_to='cruise_flyers/', null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def min_price(self):
        price = CruiseCabinPrice.objects.filter(cruise=self).aggregate(Min('price'))['price__min']
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
    
    def generate_pdf_flyer(self):
        try:
            template = get_template('cruises/cruise_flyer.html')
            context = {
                'cruise': self,
                'sessions': self.sessions.all().order_by('start_date')[:3],
                'cabin_prices': CruiseCabinPrice.objects.filter(cruise=self).select_related('cabin_type'),
                'company_logo': self.get_base64_image(self.company.logo) if self.company and self.company.logo else '',
                'cruise_image': self.get_base64_image(self.image) if self.image else '',
            }
            html = template.render(context)
            result = BytesIO()
            pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result, encoding='UTF-8')
            if pdf.err:
                logger.error(f"Error generating PDF: {pdf.err}")
                return None
            return result.getvalue()
        except Exception as e:
            logger.exception(f"Exception in generate_pdf_flyer: {str(e)}")
            return None

    def get_base64_image(self, image_field):
        if image_field and hasattr(image_field, 'path') and os.path.exists(image_field.path):
            try:
                with open(image_field.path, "rb") as image_file:
                    return base64.b64encode(image_file.read()).decode('utf-8')
            except Exception as e:
                logger.exception(f"Error processing image {image_field.path}: {str(e)}")
        return ''

class CruiseSession(BaseModel):
    cruise = models.ForeignKey(Cruise, related_name='sessions', on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    capacity = models.PositiveIntegerField()
    is_summer_special = models.BooleanField(default=False, verbose_name=_("Summer Special"))
    summer_special_type = models.CharField(
        max_length=50,
        choices=[
            ('upgrade', _('Free Cabin Upgrade')),
            ('single_discount', _('Reduced Single Cabin Supplement'))
        ],
        blank=True,
        null=True,
        verbose_name=_("Summer Special Type")
    )

    class Meta:
        unique_together = ('cruise', 'start_date', 'end_date')
        ordering = ['start_date']

    def __str__(self):
        return f"{self.cruise.name} ({self.start_date} to {self.end_date})"

    def duration(self):
        return (self.end_date - self.start_date).days + 1

    def get_summer_special_message(self):
        if self.is_summer_special:
            if self.summer_special_type == 'upgrade':
                return _("SUMMER SPECIAL: Enjoy a free cabin upgrade for this departure!")
            elif self.summer_special_type == 'single_discount':
                return _("SUMMER SPECIAL: Reduced single cabin supplement of only 20% for this departure!")
        return ""
    
class CruiseItinerary(BaseModel):
    cruise = models.ForeignKey(Cruise, related_name='itineraries', on_delete=models.CASCADE)
    day = models.PositiveIntegerField()
    port = models.ForeignKey('Port', on_delete=models.SET_NULL, null=True)
    arrival_time = models.TimeField(null=True, blank=True)
    departure_time = models.TimeField(null=True, blank=True)
    description = models.TextField()

    class Meta:
        ordering = ['cruise', 'day']
        unique_together = ['cruise', 'day']
        verbose_name_plural = "Cruise Itineraries"

    def __str__(self):
        return f"{self.cruise.name} - Day {self.day}: {self.port.name if self.port else 'At Sea'}"
    
class Port(BaseModel):
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    description = models.TextField()

    def __str__(self):
        return f"{self.name}, {self.country}"

    class Meta:
        unique_together = ['name', 'country']
    
class CabinType(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField()
    capacity = models.PositiveIntegerField()
    deck = models.CharField(max_length=50)
    equipment = models.ManyToManyField(Equipment, through='CabinTypeEquipment')

    def __str__(self):
        return f"{self.name} on {self.deck} deck"

class CabinTypeEquipment(BaseModel):
    cabin_type = models.ForeignKey(CabinType, on_delete=models.CASCADE)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ['cabin_type', 'equipment']
        verbose_name_plural = "Cabin Type Equipment"

    def __str__(self):
        return f"{self.cabin_type} - {self.equipment} (x{self.quantity})"

class CruiseCabinPrice(BaseModel):
    cruise = models.ForeignKey(Cruise, on_delete=models.CASCADE)
    cabin_type = models.ForeignKey(CabinType, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    session = models.ForeignKey(CruiseSession, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        unique_together = ['cruise', 'cabin_type', 'session']
        verbose_name_plural = "Cruise Cabin Prices"

    def __str__(self):
        return f"{self.cruise.name} - {self.cabin_type.name}: ${self.price}"
    
class Excursion(BaseModel):
    name = models.CharField(max_length=200)
    description = models.TextField()
    port = models.ForeignKey(Port, on_delete=models.CASCADE)
    duration = models.DurationField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} at {self.port.name}"

class CruiseExcursion(BaseModel):

    cruise = models.ForeignKey(Cruise, on_delete=models.CASCADE)
    excursion = models.ForeignKey(Excursion, on_delete=models.CASCADE)
    available_date = models.DateField()

    class Meta:
        unique_together = ['cruise', 'excursion', 'available_date']

    def __str__(self):
        return f"{self.excursion.name} for {self.cruise.name} on {self.available_date}"
