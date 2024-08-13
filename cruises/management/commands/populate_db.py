# yourapp/management/commands/populate_db.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from cruises.models import CruiseCompany, CruiseType, Brand, Cruise, CruiseCategory, CruiseSession, Booking
from django.contrib.auth.models import User
from django.core.files import File
from django.conf import settings
import os
from decimal import Decimal

class Command(BaseCommand):
    help = 'Populate the database with sample data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Populating database...')

        # Create cruise companies
        self.create_cruise_company(
            name='Viva Cruises',
            description='Royal Caribbean International is known for driving innovation at sea and has continuously redefined cruise vacationing since its launch in 1969.',
            website='https://www.viva-cruises.be/'
        )
        
        self.create_cruise_company(
            name='Cunard Line',
            description='The Cunard Line is a British shipping and cruise line based at Carnivl House at Southampton, England, operated by Carnival UK and owned by Carnival Corporation & plc.',
            website='https://www.cunard.com/en-gb'
        )

        # Create cruise types
        self.create_cruise_type(
            name='Maritimes',
            description='Discover the charm and beauty of the Maritime provinces.'
        )
        
        self.create_cruise_type(
            name='Rivers',
            description='Experience scenic river cruises through picturesque landscapes and historic cities.'
        )

        # Create brands
        self.create_brand(
            name='In Malta',
            description='Experience the beauty of Malta with our specialized cruise offerings.',
            website='http://inmalta.eu/001_fr.htm',
            featured=True,
            logo='brand_logos/in_malta.png'
        )
        
        self.create_brand(
            name='Cruise Selection',
            description='Your premier selection of curated cruise experiences around the world.',
            website='https://cruiseselection.be/index_LUX.htm',
            featured=True,
            logo='brand_logos/fluss_lu.png'
        )

        self.create_brand(
            name='Fluss.lu',
            description='Discover the beauty of river cruising with Fluss.lu.',
            website='https://www.fluss.lu/',
            featured=True,
            logo='https://www.fluss.lu/img/fluss-logo-1605086758.jpg'
        )

        self.stdout.write(self.style.SUCCESS('Database populated successfully!'))

    def create_cruise_company(self, name, description, website):
        company, created = CruiseCompany.objects.get_or_create(
            name=name,
            defaults={
                'description': description,
                'website': website
            }
        )
        if created:
            self.stdout.write(f'Created cruise company: {name}')
        else:
            self.stdout.write(f'Cruise company already exists: {name}')

    def create_cruise_type(self, name, description):
        cruise_type, created = CruiseType.objects.get_or_create(
            name=name,
            defaults={'description': description}
        )
        if created:
            self.stdout.write(f'Created cruise type: {name}')
        else:
            self.stdout.write(f'Cruise type already exists: {name}')

    def create_brand(self, name, description, website, featured, logo):
        brand, created = Brand.objects.get_or_create(
            name=name,
            defaults={
                'description': description,
                'website': website,
                'featured': featured,
                'logo': logo
            }
        )
        if created:
            self.stdout.write(f'Created brand: {name}')
        else:
            self.stdout.write(f'Brand already exists: {name}')