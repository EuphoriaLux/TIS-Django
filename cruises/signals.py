# cruises/signals.py

from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.apps import apps
from decimal import Decimal
from datetime import date

@receiver(post_migrate)
def create_initial_data(sender, **kwargs):
    if sender.name == 'cruises':  # Only run for our app
        # Get all required models
        Region = apps.get_model('cruises', 'Region')
        Port = apps.get_model('cruises', 'Port')
        CruiseCompany = apps.get_model('cruises', 'CruiseCompany')
        Brand = apps.get_model('cruises', 'Brand')
        Ship = apps.get_model('cruises', 'Ship')
        CruiseType = apps.get_model('cruises', 'CruiseType')
        Equipment = apps.get_model('cruises', 'Equipment')
        CabinCategory = apps.get_model('cruises', 'CabinCategory')
        Cruise = apps.get_model('cruises', 'Cruise')
        CruiseSession = apps.get_model('cruises', 'CruiseSession')
        CruiseSessionCabinPrice = apps.get_model('cruises', 'CruiseSessionCabinPrice')
        CabinEquipment = apps.get_model('cruises', 'CabinEquipment')

        print("Starting data population...")

        # Create Regions
        europe, _ = Region.objects.get_or_create(
            name='Europe',
            defaults={
                'description': 'European destinations'
            }
        )
        print("Created Europe region")
        
        benelux, _ = Region.objects.get_or_create(
            name='Benelux',
            defaults={
                'description': 'Belgium, Netherlands, and Luxembourg',
                'parent_region': europe
            }
        )
        print("Created Benelux region")

        # Create Ports
        amsterdam, _ = Port.objects.get_or_create(
            name='Amsterdam',
            country='Netherlands',
            defaults={
                'port_code': 'AMS',
                'is_embarkation_port': True,
                'is_disembarkation_port': True
            }
        )
        
        antwerp, _ = Port.objects.get_or_create(
            name='Antwerp',
            country='Belgium',
            defaults={
                'port_code': 'ANR',
                'is_embarkation_port': True,
                'is_disembarkation_port': True
            }
        )
        print("Created ports")

        # Create Cruise Company
        viva_cruises, _ = CruiseCompany.objects.get_or_create(
            name='Viva Cruises',
            defaults={
                'description': 'Royal Caribbean International is known for driving innovation at sea...',
                'website': 'https://www.viva-cruises.be/'
            }
        )
        viva_cruises.operating_regions.add(europe, benelux)
        print("Created cruise company")

        # Create Brand
        fluss_lu, _ = Brand.objects.get_or_create(
            name='Fluss.lu',
            defaults={
                'description': 'Discover the beauty of river cruising with Fluss.lu.',
                'website': 'https://www.fluss.lu/',
                'featured': True,
                'parent_company': viva_cruises,
                'market_segment': 'premium'
            }
        )
        print("Created brand")

        # Create Ship
        swiss_ruby, _ = Ship.objects.get_or_create(
            name='Swiss Ruby',
            company=viva_cruises,
            defaults={
                'brand': fluss_lu,
                'year_built': 2019,
                'passenger_capacity': 180,
                'crew_capacity': 45,
                'gross_tonnage': 2800,
                'length': Decimal('110.0'),
                'speed': Decimal('12.5')
            }
        )
        print("Created ship")

        # Create Equipment
        equipment_data = [
            {
                'name': 'Single Beds',
                'name_de': 'Einzelbetten',
                'name_fr': 'Lits simples',
                'description': 'Two single beds',
                'description_de': 'Zwei Einzelbetten',
                'description_fr': 'Deux lits simples'
            },
            {
                'name': 'Window',
                'name_de': 'Fenster',
                'name_fr': 'Fenêtre',
                'description': 'Window (non-opening)',
                'description_de': 'Fenster (nicht zu öffnen)',
                'description_fr': "Fenêtre (ne s'ouvre pas)"
            }
        ]

        equipment_objects = {}
        for data in equipment_data:
            equipment, _ = Equipment.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            equipment_objects[data['name']] = equipment
        print("Created equipment")

        # Create Cabin Categories with their equipment
        cabin_data = [
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
        ]

        created_categories = {}
        for data in cabin_data:
            category, created = CabinCategory.objects.get_or_create(
                ship=swiss_ruby,
                category_code=data['category_code'],
                defaults={**data}
            )
            created_categories[data['category_code']] = category
            
            # Add equipment to cabin
            CabinEquipment.objects.get_or_create(
                cabin_category=category,
                equipment=equipment_objects['Single Beds'],
                defaults={'quantity': 2}
            )
            CabinEquipment.objects.get_or_create(
                cabin_category=category,
                equipment=equipment_objects['Window'],
                defaults={'quantity': 1}
            )
        print("Created cabin categories")

        # Create Cruise Type
        river_cruises, _ = CruiseType.objects.get_or_create(
            name='Rivers',
            defaults={
                'description': 'Experience scenic river cruises...',
                'typical_duration': 7
            }
        )
        print("Created cruise type")

        # Create Cruise
        cruise_data = {
            'name': 'Cityhopping from Antwerpen',
            'description': 'Explore the heart of Europe...',
            'cruise_type': river_cruises,
            'ship': swiss_ruby,
            'difficulty_level': 2,
            'is_featured': True
        }

        cruise, _ = Cruise.objects.get_or_create(
            name=cruise_data['name'],
            defaults=cruise_data
        )
        print("Created cruise")

        # Create Session
        session_data = {
            'start_date': date(2025, 2, 8),
            'end_date': date(2025, 2, 12),
            'capacity': 180,
            'status': 'booking',
            'embarkation_port': amsterdam,
            'disembarkation_port': antwerp
        }

        session, _ = CruiseSession.objects.get_or_create(
            cruise=cruise,
            start_date=session_data['start_date'],
            defaults=session_data
        )
        print("Created cruise session")

        # Create Cabin Prices for each category
        price_data = {
            'EM2': {'price': 799, 'available_cabins': 10},
            'RB2': {'price': 929, 'available_cabins': 8}
        }

        for code, data in price_data.items():
            if code in created_categories:
                cabin_category = created_categories[code]
                CruiseSessionCabinPrice.objects.get_or_create(
                    cruise_session=session,
                    cabin_category=cabin_category,
                    defaults={
                        'price': Decimal(data['price']),
                        'regular_price': Decimal(data['price']),
                        'available_cabins': data['available_cabins']
                    }
                )
        print("Created cabin prices")

        print("Finished populating initial data")