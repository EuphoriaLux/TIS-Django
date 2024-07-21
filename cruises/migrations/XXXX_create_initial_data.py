from django.db import migrations
from django.core.files import File
from django.conf import settings
import os

def create_initial_data(apps, schema_editor):
    CruiseCompany = apps.get_model('cruises', 'CruiseCompany')
    CruiseType = apps.get_model('cruises', 'CruiseType')
    Brand = apps.get_model('cruises', 'Brand')
    Cruise = apps.get_model('cruises', 'Cruise')

    # Create CruiseCompanies
    carnival = CruiseCompany.objects.create(
        name="Carnival Cruise Line",
        description="Carnival Cruise Line is a leader in contemporary cruising and operates 24 ships designed to foster exceptionally fun and memorable vacation experiences at an outstanding value.",
        website="https://www.carnival.com/"
    )

    royal_caribbean = CruiseCompany.objects.create(
        name="Royal Caribbean International",
        description="Royal Caribbean International is known for driving innovation at sea and has continuously redefined cruise vacationing since its launch in 1969.",
        website="https://www.royalcaribbean.com/"
    )

    # Create CruiseTypes
    CruiseType.objects.create(
        name="Caribbean",
        description="Explore the crystal-clear waters and pristine beaches of the Caribbean islands."
    )
    CruiseType.objects.create(
        name="Mediterranean",
        description="Discover the rich history and diverse cultures of the Mediterranean region."
    )
    CruiseType.objects.create(
        name="Alaska",
        description="Experience the rugged beauty and wildlife of Alaska's stunning coastline."
    )

    # Create Brands
    carnival_brand = Brand.objects.create(
        name="Carnival",
        description="Carnival Cruise Line is all about fun vacations at sea and ashore!",
        website="https://www.carnival.com/",
        featured=True
    )
    royal_caribbean_brand = Brand.objects.create(
        name="Royal Caribbean",
        description="Royal Caribbean is an award-winning global cruise brand with a 50-year legacy of innovation and introducing industry firsts never before seen at sea.",
        website="https://www.royalcaribbean.com/",
        featured=True
    )

    # Create Cruises
    Cruise.objects.create(
        name="Caribbean Paradise",
        description="A 7-night journey through the most beautiful Caribbean islands.",
        cruise_type=CruiseType.objects.get(name="Caribbean"),
        company=carnival,
        image_url="https://example.com/caribbean_paradise.jpg"
    )
    Cruise.objects.create(
        name="Mediterranean Adventure",
        description="Explore the ancient wonders and modern delights of the Mediterranean in this 10-night cruise.",
        cruise_type=CruiseType.objects.get(name="Mediterranean"),
        company=royal_caribbean,
        image_url="https://example.com/mediterranean_adventure.jpg"
    )

def reverse_func(apps, schema_editor):
    CruiseCompany = apps.get_model('cruises', 'CruiseCompany')
    CruiseType = apps.get_model('cruises', 'CruiseType')
    Brand = apps.get_model('cruises', 'Brand')
    Cruise = apps.get_model('cruises', 'Cruise')

    CruiseCompany.objects.all().delete()
    CruiseType.objects.all().delete()
    Brand.objects.all().delete()
    Cruise.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('cruises', '0001_initial'),  # replace with your last migration
    ]

    operations = [
        migrations.RunPython(create_initial_data, reverse_func),
    ]
