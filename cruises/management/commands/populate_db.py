# cruises/management/commands/populate_db.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.files import File
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from datetime import timedelta, date
import os

from cruises.models import (
    CruiseCompany,
    CruiseType,
    Brand,
    Cruise,
    CruiseSession,
    Equipment,
    CruiseSessionCabinPrice,
    CabinCategory,
    CabinEquipment,
    Ship,
    Port,
    Region
)

class Command(BaseCommand):
    help = 'Populate the database with sample data and update existing records'

    def handle(self, *args, **kwargs):
        self.stdout.write('Populating/Updating database...')

        # Create Regions
        europe = self.create_or_update_region(
            name='Europe',
            description='European destinations'
        )
        
        benelux = self.create_or_update_region(
            name='Benelux',
            description='Belgium, Netherlands, and Luxembourg',
            parent_region=europe
        )

        # Create Ports
        amsterdam = self.create_or_update_port(
            name='Amsterdam',
            country='Netherlands',
            port_code='AMS',
            is_embarkation_port=True,
            is_disembarkation_port=True
        )
        
        antwerp = self.create_or_update_port(
            name='Antwerp',
            country='Belgium',
            port_code='ANR',
            is_embarkation_port=True,
            is_disembarkation_port=True
        )

        # Create cruise companies with regions
        viva_cruises = self.create_or_update_cruise_company(
            name='Viva Cruises',
            description='Royal Caribbean International is known for driving innovation at sea and has continuously redefined cruise vacationing since its launch in 1969.',
            website='https://www.viva-cruises.be/'
        )
        viva_cruises.operating_regions.add(europe, benelux)

        # Create brands
        fluss_lu = self.create_or_update_brand(
            name='Fluss.lu',
            description='Discover the beauty of river cruising with Fluss.lu.',
            website='https://www.fluss.lu/',
            featured=True,
            parent_company=viva_cruises,
            market_segment='premium',
            logo_path='brand_logos/fluss_lu.png'
        )

        # Create ships
        swiss_ruby = self.create_or_update_ship(
            name='Swiss Ruby',
            company=viva_cruises,
            brand=fluss_lu,
            year_built=2019,
            passenger_capacity=180,
            crew_capacity=45,
            gross_tonnage=2800,
            length=Decimal('110.0'),
            speed=Decimal('12.5')
        )

        # Create cruise types
        river_cruises = self.create_or_update_cruise_type(
            name='Rivers',
            description='Experience scenic river cruises through picturesque landscapes and historic cities.',
            typical_duration=7
        )

        # Create or update equipment
        equipment_objects = {}
        for item in self.get_equipment_list():
            equipment = self.create_or_update_equipment(*item)
            equipment_objects[item[0]] = equipment

        # Create cabin categories
        cabin_categories = self.create_cabin_categories(swiss_ruby, equipment_objects)
        
        # Create cruises and sessions with the created cabin categories
        self.create_or_update_cruises(
            ship=swiss_ruby,
            cruise_type=river_cruises,
            company=viva_cruises,
            brand=fluss_lu,
            embarkation_port=amsterdam,
            disembarkation_port=antwerp,
            cabin_categories=cabin_categories
        )

        self.stdout.write(self.style.SUCCESS('Database populated/updated successfully!'))

    def create_or_update_region(self, name, description, parent_region=None):
        region, created = Region.objects.update_or_create(
            name=name,
            defaults={
                'description': description,
                'parent_region': parent_region
            }
        )
        action = 'Created' if created else 'Updated'
        self.stdout.write(f'{action} region: {name}')
        return region

    def create_or_update_port(self, name, country, port_code, is_embarkation_port, is_disembarkation_port):
        port, created = Port.objects.update_or_create(
            name=name,
            country=country,
            defaults={
                'port_code': port_code,
                'is_embarkation_port': is_embarkation_port,
                'is_disembarkation_port': is_disembarkation_port
            }
        )
        action = 'Created' if created else 'Updated'
        self.stdout.write(f'{action} port: {name}')
        return port

    def create_or_update_cruise_company(self, name, description, website):
        company, created = CruiseCompany.objects.update_or_create(
            name=name,
            defaults={
                'description': description,
                'website': website,
            }
        )
        action = 'Created' if created else 'Updated'
        self.stdout.write(f'{action} cruise company: {name}')
        return company

    def create_or_update_brand(self, name, description, website, featured, parent_company, market_segment, logo_path):
        brand, created = Brand.objects.update_or_create(
            name=name,
            defaults={
                'description': description,
                'website': website,
                'featured': featured,
                'parent_company': parent_company,
                'market_segment': market_segment
            }
        )
        
        if logo_path:
            logo_full_path = os.path.join(settings.MEDIA_ROOT, logo_path)
            if os.path.exists(logo_full_path):
                with open(logo_full_path, 'rb') as f:
                    brand.logo.save(os.path.basename(logo_path), File(f), save=True)
                
        action = 'Created' if created else 'Updated'
        self.stdout.write(f'{action} brand: {name}')
        return brand

    def create_or_update_ship(self, name, company, brand, year_built, passenger_capacity, crew_capacity, gross_tonnage, length, speed):
        ship, created = Ship.objects.update_or_create(
            name=name,
            company=company,
            defaults={
                'brand': brand,
                'year_built': year_built,
                'passenger_capacity': passenger_capacity,
                'crew_capacity': crew_capacity,
                'gross_tonnage': gross_tonnage,
                'length': length,
                'speed': speed
            }
        )
        action = 'Created' if created else 'Updated'
        self.stdout.write(f'{action} ship: {name}')
        return ship

    def get_equipment_list(self):
        return [
            ('Single Beds', 'Einzelbetten', 'Lits simples', 'Two single beds', 'Zwei Einzelbetten', 'Deux lits simples'),
            ('Window', 'Fenster', 'Fenêtre', 'Window (non-opening)', 'Fenster (nicht zu öffnen)', "Fenêtre (ne s'ouvre pas)"),
            # Add more equipment as needed...
        ]

    def create_or_update_equipment(self, name, name_de, name_fr, description, description_de, description_fr):
        equipment, created = Equipment.objects.update_or_create(
            name=name,
            defaults={
                'name_de': name_de,
                'name_fr': name_fr,
                'description': description,
                'description_de': description_de,
                'description_fr': description_fr,
            }
        )
        action = 'Created' if created else 'Updated'
        self.stdout.write(f'{action} equipment: {name}')
        return equipment

    def create_cabin_categories(self, ship, equipment_objects):
        cabin_data = [
            {
                'name': 'Emerald | 2-Bed Cabin',
                'ship': ship,
                'description': 'Comfortable 16 m² cabin on the Emerald Deck.',
                'capacity': 2,
                'deck': 'Emerald',
                'category_code': 'EM2',
                'square_meters': Decimal('16.0'),
                'is_accessible': False,
                'has_balcony': False,
                'equipment_list': [
                    (equipment_objects['Single Beds'], 2),
                    (equipment_objects['Window'], 1),
                ]
            },
            {
                'name': 'Ruby | 2-Bed Cabin',
                'ship': ship,
                'description': 'Luxurious 16 m² cabin on the Ruby Deck.',
                'capacity': 2,
                'deck': 'Ruby',
                'category_code': 'RB2',
                'square_meters': Decimal('16.0'),
                'is_accessible': False,
                'has_balcony': False,
                'equipment_list': [
                    (equipment_objects['Single Beds'], 2),
                    (equipment_objects['Window'], 1),
                ]
            },
            {
                'name': 'Ruby | Junior Suite',
                'ship': ship,
                'description': 'Luxurious Junior Suite on the Ruby Deck.',
                'capacity': 2,
                'deck': 'Ruby',
                'category_code': 'RJS',
                'square_meters': Decimal('20.0'),
                'is_accessible': False,
                'has_balcony': True,
                'equipment_list': [
                    (equipment_objects['Single Beds'], 2),
                    (equipment_objects['Window'], 1),
                ]
            },
            {
                'name': 'Diamond | 2-Bed Cabin',
                'ship': ship,
                'description': 'Premium cabin on the Diamond Deck.',
                'capacity': 2,
                'deck': 'Diamond',
                'category_code': 'DB2',
                'square_meters': Decimal('16.0'),
                'is_accessible': True,
                'has_balcony': False,
                'equipment_list': [
                    (equipment_objects['Single Beds'], 2),
                    (equipment_objects['Window'], 1),
                ]
            },
            {
                'name': 'Diamond | Junior Suite',
                'ship': ship,
                'description': 'Luxurious Junior Suite on the Diamond Deck.',
                'capacity': 2,
                'deck': 'Diamond',
                'category_code': 'DJS',
                'square_meters': Decimal('22.0'),
                'is_accessible': True,
                'has_balcony': True,
                'equipment_list': [
                    (equipment_objects['Single Beds'], 2),
                    (equipment_objects['Window'], 1),
                ]
            }
        ]

        created_categories = {}
        for data in cabin_data:
            equipment_list = data.pop('equipment_list')
            category_code = data['category_code']
            
            cabin_category, created = CabinCategory.objects.update_or_create(
                name=data['name'],
                ship=data['ship'],
                defaults=data
            )

            # Update equipment
            CabinEquipment.objects.filter(cabin_category=cabin_category).delete()
            for equipment, quantity in equipment_list:
                CabinEquipment.objects.create(
                    cabin_category=cabin_category,
                    equipment=equipment,
                    quantity=quantity
                )

            created_categories[category_code] = cabin_category
            action = 'Created' if created else 'Updated'
            self.stdout.write(f'{action} cabin category: {data["name"]}')
            
        return created_categories

    def create_or_update_cruise_type(self, name, description, typical_duration):
        cruise_type, created = CruiseType.objects.update_or_create(
            name=name,
            defaults={
                'description': description,
                'typical_duration': typical_duration
            }
        )
        action = 'Created' if created else 'Updated'
        self.stdout.write(f'{action} cruise type: {name}')
        return cruise_type

    def create_or_update_cruises(self, ship, cruise_type, company, brand, embarkation_port, disembarkation_port, cabin_categories):
        cruises_data = [
            {
                'name': 'Cityhopping from Antwerpen',
                'description': 'Explore the heart of Europe along the beautiful waterways.',
                'difficulty_level': 2,
                'is_featured': True,
                'sessions': [
                    {
                        'start_date': date(2025, 2, 8),
                        'end_date': date(2025, 2, 12),
                        'capacity': 180,
                        'status': 'booking',
                        'cabin_prices': {
                            'EM2': {'price': 799, 'available_cabins': 10},
                            'RB2': {'price': 929, 'available_cabins': 8},
                            'RJS': {'price': 1029, 'available_cabins': 6},
                            'DB2': {'price': 999, 'available_cabins': 8},
                            'DJS': {'price': 1199, 'available_cabins': 4}
                        }
                    },
                    {
                        'start_date': date(2025, 2, 12),
                        'end_date': date(2025, 2, 16),
                        'capacity': 180,
                        'status': 'booking',
                        'cabin_prices': {
                            'EM2': {'price': 799, 'available_cabins': 10},
                            'RB2': {'price': 929, 'available_cabins': 8},
                            'RJS': {'price': 1029, 'available_cabins': 6},
                            'DB2': {'price': 999, 'available_cabins': 8},
                            'DJS': {'price': 1199, 'available_cabins': 4}
                        }
                    }
                ]
            },
            {
                'name': 'Voyage in Donau Delta',
                'description': 'Experience the beauty of the Danube Delta.',
                'difficulty_level': 3,
                'is_featured': True,
                'sessions': [
                    {
                        'start_date': date(2025, 5, 8),
                        'end_date': date(2025, 5, 24),
                        'capacity': 180,
                        'status': 'booking',
                        'cabin_prices': {
                            'EM2': {'price': 4499, 'available_cabins': 8},
                            'RB2': {'price': 4999, 'available_cabins': 6},
                            'DB2': {'price': 5399, 'available_cabins': 4},
                            'DJS': {'price': 6699, 'available_cabins': 2}
                        }
                    }
                ]
            }
        ]

        for cruise_data in cruises_data:
            # Make a copy of sessions data since we'll be popping it
            sessions = cruise_data.pop('sessions')
            
            # Create or update the cruise
            cruise, created = Cruise.objects.update_or_create(
                name=cruise_data['name'],
                defaults={
                    **cruise_data,
                    'cruise_type': cruise_type,
                    'ship': ship
                }
            )

            # Process each session
            for session_data in sessions:
                cabin_prices = session_data.pop('cabin_prices')
                session, session_created = CruiseSession.objects.update_or_create(
                    cruise=cruise,
                    start_date=session_data['start_date'],
                    defaults={
                        **session_data,
                        'embarkation_port': embarkation_port,
                        'disembarkation_port': disembarkation_port
                    }
                )

                # Process cabin prices for the session
                for category_code, price_data in cabin_prices.items():
                    if category_code not in cabin_categories:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Skipping price for unknown cabin category code: {category_code}'
                            )
                        )
                        continue
                        
                    cabin_category = cabin_categories[category_code]
                    CruiseSessionCabinPrice.objects.update_or_create(
                        cruise_session=session,
                        cabin_category=cabin_category,
                        defaults={
                            'price': Decimal(price_data['price']),
                            'regular_price': Decimal(price_data['price']),
                            'available_cabins': price_data['available_cabins']
                        }
                    )

            action = 'Created' if created else 'Updated'
            self.stdout.write(f'{action} cruise: {cruise_data["name"]}')
        cruises_data = [
            {
                'name': 'Cityhopping from Antwerpen',
                'description': 'Explore the heart of Europe along the beautiful waterways.',
                'difficulty_level': 2,
                'is_featured': True,
                'sessions': [
                    {
                        'start_date': date(2025, 2, 8),
                        'end_date': date(2025, 2, 12),
                        'capacity': 180,
                        'status': 'booking',
                        'cabin_prices': {
                            'EM2': {'price': 799, 'available_cabins': 10},
                            'RB2': {'price': 929, 'available_cabins': 8},
                            'RJS': {'price': 1029, 'available_cabins': 6},
                            'DB2': {'price': 999, 'available_cabins': 8},
                            'DJS': {'price': 1199, 'available_cabins': 4}
                        }
                    },
                    {
                        'start_date': date(2025, 2, 12),
                        'end_date': date(2025, 2, 16),
                        'capacity': 180,
                        'status': 'booking',
                        'cabin_prices': {
                            'EM2': {'price': 799, 'available_cabins': 10},
                            'RB2': {'price': 929, 'available_cabins': 8},
                            'RJS': {'price': 1029, 'available_cabins': 6},
                            'DB2': {'price': 999, 'available_cabins': 8},
                            'DJS': {'price': 1199, 'available_cabins': 4}
                        }
                    }
                ]
            },
            {
                'name': 'Voyage in Donau Delta',
                'description': 'Experience the beauty of the Danube Delta.',
                'difficulty_level': 3,
                'is_featured': True,
                'sessions': [
                    {
                        'start_date': date(2025, 5, 8),
                        'end_date': date(2025, 5, 24),
                        'capacity': 180,
                        'status': 'booking',
                        'cabin_prices': {
                            'EM2': {'price': 4499, 'available_cabins': 8},
                            'RB2': {'price': 4999, 'available_cabins': 6},
                            'DB2': {'price': 5399, 'available_cabins': 4},
                            'DJS': {'price': 6699, 'available_cabins': 2}
                        }
                    }
                ]
            }
        ]

        for cruise_data in cruises_data:
            sessions = cruise_data.pop('sessions')
            cruise, created = Cruise.objects.update_or_create(
                name=cruise_data['name'],
                defaults={
                    **cruise_data,
                    'cruise_type': cruise_type,
                    'ship': ship
                }
            )

            for session_data in sessions:
                cabin_prices = session_data.pop('cabin_prices')
                session, session_created = CruiseSession.objects.update_or_create(
                    cruise=cruise,
                    start_date=session_data['start_date'],
                    defaults={
                        **session_data,
                        'embarkation_port': embarkation_port,
                        'disembarkation_port': disembarkation_port
                    }
                )

                for category_code, price_data in cabin_prices.items():
                    if category_code not in cabin_categories:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Skipping price for unknown cabin category code: {category_code}'
                            )
                        )
                        continue
                        
                    cabin_category = cabin_categories[category_code]
                    CruiseSessionCabinPrice.objects.update_or_create(
                        cruise_session=session,
                        cabin_category=cabin_category,
                        defaults={
                            'price': Decimal(price_data['price']),
                            'regular_price': Decimal(price_data['price']),
                            'available_cabins': price_data['available_cabins']
                        }
                    )

            action = 'Created' if created else 'Updated'
            self.stdout.write(f'{action} cruise: {cruise_data["name"]}')
            sessions = cruise_data.pop('sessions')
            cruise, created = Cruise.objects.update_or_create(
                name=cruise_data['name'],
                defaults={
                    **cruise_data,
                    'cruise_type': cruise_type,
                    'ship': ship
                }
            )

            for session_data in sessions:
                cabin_prices = session_data.pop('cabin_prices')
                session, session_created = CruiseSession.objects.update_or_create(
                    cruise=cruise,
                    start_date=session_data['start_date'],
                    defaults={
                        **session_data,
                        'embarkation_port': embarkation_port,
                        'disembarkation_port': disembarkation_port
                    }
                )

                for category_code, price_data in cabin_prices.items():
                    cabin_category = CabinCategory.objects.get(category_code=category_code, ship=ship)
                    CruiseSessionCabinPrice.objects.update_or_create(
                        cruise_session=session,
                        cabin_category=cabin_category,
                        defaults={
                            'price': Decimal(price_data['price']),
                            'regular_price': Decimal(price_data['price']),
                            'available_cabins': price_data['available_cabins']
                        }
                    )

            action = 'Created' if created else 'Updated'
            self.stdout.write(f'{action} cruise: {cruise_data["name"]}')