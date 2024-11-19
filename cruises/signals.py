# cruises/signals.py

from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.apps import apps
from decimal import Decimal
from datetime import date

@receiver(post_migrate)
def create_initial_data(sender, **kwargs):
    if sender.name == 'cruises':  # Only run for our app
        try:
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

            # Check if we need to run the population
            if CruiseSession.objects.count() > 10:  # Skip if we already have many sessions
                print("Database already populated, skipping...")
                return

            print("Starting data population or update...")

            # Create Regions
            europe, _ = Region.objects.get_or_create(
                name='Europe',
                defaults={
                    'description': 'European destinations including scenic rivers and historic cities'
                }
            )
            
            benelux, _ = Region.objects.get_or_create(
                name='Benelux',
                defaults={
                    'description': 'Belgium, Netherlands, and Luxembourg - heart of European waterways',
                    'parent_region': europe
                }
            )
            
            rhine_region, _ = Region.objects.get_or_create(
                name='Rhine Valley',
                defaults={
                    'description': 'The romantic Rhine Valley with its castles and vineyards',
                    'parent_region': europe
                }
            )
            print("Created regions")

            # Create Ports
            ports_data = [
                {
                    'name': 'Amsterdam',
                    'country': 'Netherlands',
                    'port_code': 'AMS',
                    'is_embarkation_port': True,
                    'is_disembarkation_port': True
                },
                {
                    'name': 'Antwerp',
                    'country': 'Belgium',
                    'port_code': 'ANR',
                    'is_embarkation_port': True,
                    'is_disembarkation_port': True
                },
                {
                    'name': 'Rotterdam',
                    'country': 'Netherlands',
                    'port_code': 'RTM',
                    'is_embarkation_port': True,
                    'is_disembarkation_port': True
                },
                {
                    'name': 'Cologne',
                    'country': 'Germany',
                    'port_code': 'CGN',
                    'is_embarkation_port': True,
                    'is_disembarkation_port': True
                }
            ]

            ports = {}
            for port_data in ports_data:
                port, _ = Port.objects.get_or_create(
                    name=port_data['name'],
                    country=port_data['country'],
                    defaults=port_data
                )
                ports[port_data['name']] = port
            print("Created ports")

            # Create Cruise Company
            viva_cruises, _ = CruiseCompany.objects.get_or_create(
                name='Viva Cruises',
                defaults={
                    'description': 'Premium river cruise experiences across Europe',
                    'website': 'https://www.viva-cruises.com/'
                }
            )
            viva_cruises.operating_regions.add(europe, benelux, rhine_region)
            print("Created cruise company")

            # Create Brand
            fluss_lu, _ = Brand.objects.get_or_create(
                name='Fluss.lu',
                defaults={
                    'description': 'Discover the beauty of river cruising with Fluss.lu',
                    'website': 'https://www.fluss.lu/',
                    'featured': True,
                    'parent_company': viva_cruises,
                    'market_segment': 'premium'
                }
            )
            print("Created brand")

            # Create Ships
            ships_data = [
                {
                    'name': 'Swiss Ruby',
                    'year_built': 2019,
                    'passenger_capacity': 180,
                    'crew_capacity': 45,
                    'gross_tonnage': 2800,
                    'length': Decimal('110.0'),
                    'speed': Decimal('12.5')
                },
                {
                    'name': 'Viva Gloria',
                    'year_built': 2020,
                    'passenger_capacity': 190,
                    'crew_capacity': 48,
                    'gross_tonnage': 3000,
                    'length': Decimal('115.0'),
                    'speed': Decimal('13.0')
                },
                {
                    'name': 'Viva Two',
                    'year_built': 2021,
                    'passenger_capacity': 200,
                    'crew_capacity': 50,
                    'gross_tonnage': 3200,
                    'length': Decimal('120.0'),
                    'speed': Decimal('13.5')
                }
            ]

            ships = {}
            for ship_data in ships_data:
                ship, _ = Ship.objects.get_or_create(
                    name=ship_data['name'],
                    company=viva_cruises,
                    defaults={
                        **ship_data,
                        'brand': fluss_lu
                    }
                )
                ships[ship_data['name']] = ship
            print("Created ships")

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
                    'name_de': 'Einzelbetten',
                    'name_fr': 'Lits simples',
                    'description': 'Two single beds',
                    'description_de': 'Zwei Einzelbetten',
                    'description_fr': 'Deux lits simples'
                },
                {
                    'name': 'French Balcony',
                    'name_de': 'Einzelbetten',
                    'name_fr': 'Lits simples',
                    'description': 'Two single beds',
                    'description_de': 'Zwei Einzelbetten',
                    'description_fr': 'Deux lits simples'
                },
            
                # [Other equipment items remain the same]
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
            cabin_categories_data = [
                {
                    'name': 'Emerald | 2-Bed Cabin',
                    'description': 'Comfortable 16 m² cabin on the Emerald Deck.',
                    'capacity': 2,
                    'deck': 'Emerald',
                    'category_code': 'EM2',
                    'square_meters': Decimal('16.0'),
                    'is_accessible': False,
                    'has_balcony': False,
                    'equipment': ['Single Beds', 'Window']
                },
                {
                    'name': 'Ruby | 2-Bed Cabin',
                    'description': 'Luxurious 16 m² cabin on the Ruby Deck.',
                    'capacity': 2,
                    'deck': 'Ruby',
                    'category_code': 'RB2',
                    'square_meters': Decimal('16.0'),
                    'is_accessible': False,
                    'has_balcony': True,
                    'equipment': ['Single Beds', 'French Balcony']
                },
                {
                    'name': 'Diamond | 2-Bed Cabin',
                    'description': 'Premium 18 m² cabin on the Diamond Deck.',
                    'capacity': 2,
                    'deck': 'Diamond',
                    'category_code': 'DI2',
                    'square_meters': Decimal('18.0'),
                    'is_accessible': True,
                    'has_balcony': True,
                    'equipment': ['Single Beds', 'French Balcony']
                }
            ]

            # Create categories for each ship
            created_categories = {}
            for ship in ships.values():
                for data in cabin_categories_data:
                    # Create a deep copy of the data to avoid modifying the original
                    category_data = data.copy()
                    equipment_list = category_data.pop('equipment')
                    
                    category, created = CabinCategory.objects.get_or_create(
                        ship=ship,
                        category_code=category_data['category_code'],
                        defaults=category_data
                    )
                    created_categories[f"{ship.name}_{category_data['category_code']}"] = category
                    
                    # Add equipment to cabin
                    for equip_name in equipment_list:
                        CabinEquipment.objects.get_or_create(
                            cabin_category=category,
                            equipment=equipment_objects[equip_name],
                            defaults={'quantity': 2 if equip_name == 'Single Beds' else 1}
                        )
            print("Created cabin categories")

            # Create Cruise Types
            cruise_types_data = [
                {
                    'name': 'Rivers',
                    'description': 'Experience scenic river cruises along Europe\'s most beautiful waterways',
                    'typical_duration': 7
                },
                {
                    'name': 'City Breaks',
                    'description': 'Short cruises visiting major European cities',
                    'typical_duration': 4
                },
                {
                    'name': 'Cultural Heritage',
                    'description': 'Explore historical sites and cultural landmarks',
                    'typical_duration': 8
                }
            ]

            cruise_types = {}
            for data in cruise_types_data:
                cruise_type, _ = CruiseType.objects.get_or_create(
                    name=data['name'],
                    defaults=data
                )
                cruise_types[data['name']] = cruise_type
            print("Created cruise types")

            # Define cruises with their sessions
            cruises_data = [
                {
                    'name': 'Cityhopping from Antwerpen',
                    'description': 'Explore the heart of Europe with stops in major cities',
                    'cruise_type': cruise_types['City Breaks'],
                    'ship': ships['Swiss Ruby'],
                    'difficulty_level': 2,
                    'is_featured': True,
                    'regions': [benelux],
                    'sessions': [
                        {
                            'start_date': date(2025, 2, 12),
                            'end_date': date(2025, 2, 16),
                            'embarkation_port': ports['Antwerp'],
                            'disembarkation_port': ports['Antwerp']
                        },
                        {
                            'start_date': date(2025, 2, 16),
                            'end_date': date(2025, 2, 20),
                            'embarkation_port': ports['Antwerp'],
                            'disembarkation_port': ports['Antwerp']
                        }
                    ]
                },
                {
                    'name': 'Rhine Valley Explorer',
                    'description': 'Journey through the scenic Rhine Valley',
                    'cruise_type': cruise_types['Rivers'],
                    'ship': ships['Viva Gloria'],
                    'difficulty_level': 1,
                    'is_featured': True,
                    'regions': [rhine_region],
                    'sessions': [
                        {
                            'start_date': date(2025, 4, 1),
                            'end_date': date(2025, 4, 7),
                            'embarkation_port': ports['Cologne'],
                            'disembarkation_port': ports['Amsterdam']
                        },
                        {
                            'start_date': date(2025, 5, 1),
                            'end_date': date(2025, 5, 7),
                            'embarkation_port': ports['Amsterdam'],
                            'disembarkation_port': ports['Cologne']
                        }
                    ]
                }
            ]

            def get_seasonal_price(base_price, start_date):
                if start_date.month in [6, 7, 8]:  # Peak season
                    return base_price * Decimal('1.25')
                elif start_date.month in [4, 5, 9]:  # Shoulder season
                    return base_price * Decimal('1.1')
                return base_price  # Low season

            # Create cruises and their sessions
            for cruise_data in cruises_data:
                sessions = cruise_data.pop('sessions')
                regions = cruise_data.pop('regions')
                
                cruise, _ = Cruise.objects.get_or_create(
                    name=cruise_data['name'],
                    defaults=cruise_data
                )
                cruise.regions.set(regions)
                
                # Create sessions for this cruise
                for session_data in sessions:
                    session, _ = CruiseSession.objects.get_or_create(
                        cruise=cruise,
                        start_date=session_data['start_date'],
                        defaults={
                            **session_data,
                            'capacity': cruise.ship.passenger_capacity,
                            'status': 'booking'
                        }
                    )

                    # Create cabin prices for all categories of this ship
                    for category_key, category in created_categories.items():
                        if category.ship == cruise.ship:
                            base_price = Decimal('799') if 'EM2' in category_key else \
                                    Decimal('929') if 'RB2' in category_key else \
                                    Decimal('1099')
                            
                            seasonal_price = get_seasonal_price(base_price, session.start_date)
                            
                            CruiseSessionCabinPrice.objects.get_or_create(
                                cruise_session=session,
                                cabin_category=category,
                                defaults={
                                    'price': seasonal_price,
                                    'regular_price': seasonal_price * Decimal('1.15'),
                                    'available_cabins': 10,
                                    'is_early_bird': True,
                                    'early_bird_deadline': date(2024, 12, 31),
                                    'single_supplement': Decimal('50.00'),
                                    'third_person_discount': Decimal('30.00')
                                }
                            )

                print(f"Created cruise {cruise.name} with {len(sessions)} sessions")

            print("Finished creating all cruises and sessions")

        except Exception as e:
            print(f"Error during data population: {str(e)}")
            raise  # Re-raise the exception to see the full traceback