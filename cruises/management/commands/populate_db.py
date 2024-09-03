# yourapp/management/commands/populate_db.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from cruises.models import CruiseCompany, CruiseType, Brand, Cruise, CruiseSession, Equipment, CruiseCabinPrice, CabinType, CabinTypeEquipment
from django.contrib.auth.models import User
from django.core.files import File
from django.conf import settings
import os
from decimal import Decimal
from datetime import timedelta
from datetime import date

class Command(BaseCommand):
    help = 'Populate the database with sample data and update existing records'

    def handle(self, *args, **kwargs):
        self.stdout.write('Populating/Updating database...')

        # Create or update cruise companies
        self.create_or_update_cruise_company(
            name='Viva Cruises',
            description='Royal Caribbean International is known for driving innovation at sea and has continuously redefined cruise vacationing since its launch in 1969.',
            website='https://www.viva-cruises.be/'
        )
        
        self.create_or_update_cruise_company(
            name='Cunard Line',
            description='The Cunard Line is a British shipping and cruise line based at Carnivl House at Southampton, England, operated by Carnival UK and owned by Carnival Corporation & plc.',
            website='https://www.cunard.com/en-gb'
        )

        # Create or update cruise types
        self.create_or_update_cruise_type(
            name='Maritimes',
            description='Discover the charm and beauty of the Maritime provinces.'
        )
        
        self.create_or_update_cruise_type(
            name='Rivers',
            description='Experience scenic river cruises through picturesque landscapes and historic cities.'
        )

        # Create or update brands
        self.create_or_update_brand(
            name='In Malta',
            description='Experience the beauty of Malta with our specialized cruise offerings.',
            website='http://inmalta.eu/001_fr.htm',
            featured=True,
            logo='brand_logos/in_malta.png'
        )
        
        self.create_or_update_brand(
            name='Fleuves du Monde',
            description='Your premier selection of curated cruise experiences around the world.',
            website='http://www.fleuvesdumonde.eu/index_fr.htm',
            featured=True,
            logo='brand_logos/logo_fleuvesdumonde.jpg'
        )

        self.create_or_update_brand(
            name='Cruise Selection',
            description='Your premier selection of curated cruise experiences around the world.',
            website='https://cruiseselection.be/index_LUX.htm',
            featured=True,
            logo='brand_logos/cruise_selection.png'
        )

        self.create_or_update_brand(
            name='Fluss.lu',
            description='Discover the beauty of river cruising with Fluss.lu.',
            website='https://www.fluss.lu/',
            featured=True,
            logo='brand_logos/fluss_lu.png'
        )

        self.create_or_update_brand(
            name='In Luxembourg',
            description='Discover the beauty of Luxembourg.',
            website='http://inluxembourg.eu/index_nl.htm',
            featured=True,
            logo='brand_logos/inluxembourg_logo.png'
        )

        # Create or update equipment
        equipment_list = [
            ('Single Beds', 'Einzelbetten', 'Lits simples', 'Two single beds (can be separated upon request)', 'Zwei Einzelbetten (auf Wunsch auseinander gestellt)', 'Deux lits simples (peuvent être séparés sur demande)'),
            ('Window', 'Fenster', 'Fenêtre', 'Window (non-opening)', 'Fenster (nicht zu öffnen)', "Fenêtre (ne s'ouvre pas)"),
            ('Seating', 'Sitzgelegenheit', 'Sièges', 'Table and two chairs', 'Tisch und zwei Sessel', 'Table et deux chaises'),
            ('Cosmetics', 'Kosmetikprodukte', 'Produits cosmétiques', 'RITUALS® beauty products', 'Beauty Produkte von RITUALS®', 'Produits de beauté RITUALS®'),
            ('TV', 'Fernseher', 'Télévision', '32" LED TV', '32" LED TV', 'Téléviseur LED 32"'),
            ('Minibar', 'Minibar', 'Mini-bar', 'Minibar with complimentary water, beer, and soft drinks, refilled daily', 'Minibar mit kostenfreiem Wasser, Bier und Softdrinks, täglich neu befüllt', 'Mini-bar avec eau, bière et boissons gazeuses gratuites, réapprovisionné quotidiennement'),
            ('Coffee Machine', 'Kaffeemaschine', 'Machine à café', 'Nespresso® machine', 'Nespresso®-Maschine', 'Machine Nespresso®'),
            ('Hair Dryer', 'Haartrockner', 'Sèche-cheveux', 'Hair dryer', 'Haartrockner', 'Sèche-cheveux'),
            ('Wi-Fi', 'WLAN', 'Wi-Fi', 'Free Wi-Fi access', 'Kostenfreier WLAN-Zugang', 'Accès Wi-Fi gratuit'),
            ('Other', 'Sonstiges', 'Autres', 'Telephone, safe, and air conditioning/heating', 'Telefon, Safe und Klimaanlage/Heizung', 'Téléphone, coffre-fort et climatisation/chauffage'),
            ('Bathroom', 'Badezimmer', 'Salle de bain', 'Bathroom with shower', 'Badezimmer mit Dusche', 'Salle de bain avec douche'),
            ('Storage', 'Stauraum', 'Rangement', 'Generous storage space in closets and under the bed', 'Grosszügig bemessener Stauraum in Schränken und unter dem Bett', 'Espace de rangement généreux dans les placards et sous le lit'),
        ]

        equipment_objects = {}
        for item in equipment_list:
            equipment = self.create_or_update_equipment(*item)
            equipment_objects[item[0]] = equipment

        self.create_or_update_cabin_type(
            name='Emerald | 2-Bed Cabin',
            description='Comfortable 16 m² cabin on the Emerald Deck. Furnished with two single beds or one double bed, a large window (non-opening), and all VIVA All-Inclusive amenities. An excellent choice for guests seeking a good balance between location and price.',
            capacity=2,
            deck='Emerald',
            equipment_list=[
                (equipment_objects['Single Beds'], 2),
                (equipment_objects['Window'], 1),
                (equipment_objects['Seating'], 1),
                (equipment_objects['Cosmetics'], 1),
                (equipment_objects['TV'], 1),
                (equipment_objects['Minibar'], 1),
                (equipment_objects['Coffee Machine'], 1),
                (equipment_objects['Hair Dryer'], 1),
                (equipment_objects['Wi-Fi'], 1),
                (equipment_objects['Other'], 1),
                (equipment_objects['Bathroom'], 1),
                (equipment_objects['Storage'], 1),
            ]
        )

        # Create or update cabin types with equipment
        self.create_or_update_cabin_type(
            name='Ruby | 2-Bed Cabin',
            description='Luxurious 16 m² cabin on the Ruby Deck. Equipped with two single beds or one double bed, a large panoramic window (non-opening), and all VIVA All-Inclusive amenities. Ideal for couples or friends who appreciate comfort and scenic views.',
            capacity=2,
            deck='Ruby',
            equipment_list=[
                (equipment_objects['Single Beds'], 2),
                (equipment_objects['Window'], 1),
                (equipment_objects['Seating'], 1),
                (equipment_objects['Cosmetics'], 1),
                (equipment_objects['TV'], 1),
                (equipment_objects['Minibar'], 1),
                (equipment_objects['Coffee Machine'], 1),
                (equipment_objects['Hair Dryer'], 1),
                (equipment_objects['Wi-Fi'], 1),
                (equipment_objects['Other'], 1),
                (equipment_objects['Bathroom'], 1),
                (equipment_objects['Storage'], 1),
            ]
        )

        self.create_or_update_cabin_type(
            name='Ruby | 2-Bed Cabin Rear',
            description='Luxurious 16 m² cabin on the Ruby Deck. Equipped with two single beds or one double bed, a large panoramic window (non-opening), and all VIVA All-Inclusive amenities. Ideal for couples or friends who appreciate comfort and scenic views.',
            capacity=2,
            deck='Ruby',
            equipment_list=[
                (equipment_objects['Single Beds'], 2),
                (equipment_objects['Window'], 1),
                (equipment_objects['Seating'], 1),
                (equipment_objects['Cosmetics'], 1),
                (equipment_objects['TV'], 1),
                (equipment_objects['Minibar'], 1),
                (equipment_objects['Coffee Machine'], 1),
                (equipment_objects['Hair Dryer'], 1),
                (equipment_objects['Wi-Fi'], 1),
                (equipment_objects['Other'], 1),
                (equipment_objects['Bathroom'], 1),
                (equipment_objects['Storage'], 1),
            ]
        )

        self.create_or_update_cabin_type(
            name='Ruby | Junior Suite',
            description='Luxurious 16 m² cabin on the Ruby Deck. Equipped with two single beds or one double bed, a large panoramic window (non-opening), and all VIVA All-Inclusive amenities. Ideal for couples or friends who appreciate comfort and scenic views.',
            capacity=2,
            deck='Ruby',
            equipment_list=[
                (equipment_objects['Single Beds'], 2),
                (equipment_objects['Window'], 1),
                (equipment_objects['Seating'], 1),
                (equipment_objects['Cosmetics'], 1),
                (equipment_objects['TV'], 1),
                (equipment_objects['Minibar'], 1),
                (equipment_objects['Coffee Machine'], 1),
                (equipment_objects['Hair Dryer'], 1),
                (equipment_objects['Wi-Fi'], 1),
                (equipment_objects['Other'], 1),
                (equipment_objects['Bathroom'], 1),
                (equipment_objects['Storage'], 1),
            ]
        )

        self.create_or_update_cabin_type(
            name='Diamond | 2-Bed Cabin',
            description='Generous 24 m² suite on the exclusive Diamond Deck. Enjoy luxurious space, a separate living room, a bedroom with a double bed, a large panoramic window (non-opening), and all VIVA All-Inclusive Premium services. The perfect choice for guests desiring the utmost comfort and exclusivity.',
            capacity=2,
            deck='Diamond',
            equipment_list=[
                (equipment_objects['Single Beds'], 2),
                (equipment_objects['Window'], 1),
                (equipment_objects['Seating'], 1),
                (equipment_objects['Cosmetics'], 1),
                (equipment_objects['TV'], 1),
                (equipment_objects['Minibar'], 1),
                (equipment_objects['Coffee Machine'], 1),
                (equipment_objects['Hair Dryer'], 1),
                (equipment_objects['Wi-Fi'], 1),
                (equipment_objects['Other'], 1),
                (equipment_objects['Bathroom'], 1),
                (equipment_objects['Storage'], 1),
            ]
        )

        self.create_or_update_cabin_type(
            name='Diamond | Junior Suite',
            description='Generous 24 m² suite on the exclusive Diamond Deck. Enjoy luxurious space, a separate living room, a bedroom with a double bed, a large panoramic window (non-opening), and all VIVA All-Inclusive Premium services. The perfect choice for guests desiring the utmost comfort and exclusivity.',
            capacity=2,
            deck='Diamond',
            equipment_list=[
                (equipment_objects['Single Beds'], 2),
                (equipment_objects['Window'], 1),
                (equipment_objects['Seating'], 1),
                (equipment_objects['Cosmetics'], 1),
                (equipment_objects['TV'], 1),
                (equipment_objects['Minibar'], 1),
                (equipment_objects['Coffee Machine'], 1),
                (equipment_objects['Hair Dryer'], 1),
                (equipment_objects['Wi-Fi'], 1),
                (equipment_objects['Other'], 1),
                (equipment_objects['Bathroom'], 1),
                (equipment_objects['Storage'], 1),
            ]
        )

        self.create_or_update_cabin_type(
            name='Diamond | Balcon Suite',
            description='Generous 24 m² suite on the exclusive Diamond Deck. Enjoy luxurious space, a separate living room, a bedroom with a double bed, a large panoramic window (non-opening), and all VIVA All-Inclusive Premium services. The perfect choice for guests desiring the utmost comfort and exclusivity.',
            capacity=2,
            deck='Diamond',
            equipment_list=[
                (equipment_objects['Single Beds'], 2),
                (equipment_objects['Window'], 1),
                (equipment_objects['Seating'], 1),
                (equipment_objects['Cosmetics'], 1),
                (equipment_objects['TV'], 1),
                (equipment_objects['Minibar'], 1),
                (equipment_objects['Coffee Machine'], 1),
                (equipment_objects['Hair Dryer'], 1),
                (equipment_objects['Wi-Fi'], 1),
                (equipment_objects['Other'], 1),
                (equipment_objects['Bathroom'], 1),
                (equipment_objects['Storage'], 1),
            ]
        )
        
        # create or update cruises
        self.create_or_update_cruises()

        self.stdout.write(self.style.SUCCESS('Database populated/updated successfully!'))

    def create_or_update_cruise_company(self, name, description, website):
        company, created = CruiseCompany.objects.update_or_create(
            name=name,
            defaults={
                'description': description,
                'website': website
            }
        )
        if created:
            self.stdout.write(f'Created cruise company: {name}')
        else:
            self.stdout.write(f'Updated cruise company: {name}')

    def create_or_update_cruise_type(self, name, description):
        cruise_type, created = CruiseType.objects.update_or_create(
            name=name,
            defaults={'description': description}
        )
        if created:
            self.stdout.write(f'Created cruise type: {name}')
        else:
            self.stdout.write(f'Updated cruise type: {name}')

    def create_or_update_brand(self, name, description, website, featured, logo):
        brand, created = Brand.objects.update_or_create(
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
            self.stdout.write(f'Updated brand: {name}')

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
        if created:
            self.stdout.write(f'Created equipment: {name}')
        else:
            self.stdout.write(f'Updated equipment: {name}')
        return equipment

    def create_or_update_cabin_type(self, name, description, capacity, deck, equipment_list):
        cabin_type, created = CabinType.objects.update_or_create(
            name=name,
            defaults={
                'description': description,
                'capacity': capacity,
                'deck': deck,
            }
        )
        
        # Clear existing equipment associations
        CabinTypeEquipment.objects.filter(cabin_type=cabin_type).delete()
        
        # Add new equipment associations
        for equipment, quantity in equipment_list:
            CabinTypeEquipment.objects.create(
                cabin_type=cabin_type,
                equipment=equipment,
                quantity=quantity
            )
        
        if created:
            self.stdout.write(f'Created cabin type: {name}')
        else:
            self.stdout.write(f'Updated cabin type: {name}')

    def create_or_update_cruise_cabin_price(self, cruise, cabin_type, price, session):
        cruise_cabin_price, created = CruiseCabinPrice.objects.update_or_create(
            cruise=cruise,
            cabin_type=cabin_type,
            session=session,
            defaults={'price': price}
        )
        if created:
            self.stdout.write(f'Created cruise cabin price: {cruise.name} - {cabin_type.name} - {session.start_date}')
        else:
            self.stdout.write(f'Updated cruise cabin price: {cruise.name} - {cabin_type.name} - {session.start_date}')

    def create_or_update_cruises(self):
        cruises_data = [
            {
                'name': 'Cityhopping from Antwerpen',
                'description': 'Explore the heart of Europe along the beautiful Danube.',
                'cruise_type': 'Rivers',
                'company': 'Viva Cruises',
                'brand': 'Fluss.lu',
                'image_url': 'https://example.com/danube_delights.jpg',
                'sessions': [
                    {
                        'start_date': date(2025, 2, 8),
                        'end_date': date(2025, 2, 12),
                        'capacity': 180,
                        'prices': {
                            'Emerald | 2-Bed Cabin': 799,
                            'Ruby | 2-Bed Cabin': 929,
                            'Ruby | Junior Suite': 1029,
                            'Diamond | 2-Bed Cabin': 999,
                            'Diamond | Junior Suite': 1199, 
                            'Diamond | Balcon Suite': 1299,
                        }
                    },
                    {
                        'start_date': date(2025, 2, 12),
                        'end_date': date(2025, 2, 16),
                        'capacity': 180,
                        'prices': {
                            'Emerald | 2-Bed Cabin': 799,
                            'Ruby | 2-Bed Cabin': 929,
                            'Ruby | Junior Suite': 1029,
                            'Diamond | 2-Bed Cabin': 999,
                            'Diamond | Junior Suite': 1199, 
                            'Diamond | Balcon Suite': 1299,
                        }
                    },
                    {
                        'start_date': date(2025, 2, 20),
                        'end_date': date(2025, 2, 24),
                        'capacity': 180,
                        'prices': {
                            'Emerald | 2-Bed Cabin': 799,
                            'Ruby | 2-Bed Cabin': 929,
                            'Ruby | Junior Suite': 1029,
                            'Diamond | 2-Bed Cabin': 999,
                            'Diamond | Junior Suite': 1199, 
                            'Diamond | Balcon Suite': 1299,
                        }
                    }
                ]
            },
            {
                'name': 'Voyage in Donau Delta',
                'description': 'Explore the heart of Europe along the beautiful Danube.',
                'cruise_type': 'Rivers',
                'company': 'Viva Cruises',
                'brand': 'Fluss.lu',
                'image_url': 'https://example.com/danube_delights.jpg',
                'sessions': [
                    {
                        'start_date': date(2025, 5, 8),
                        'end_date': date(2025, 5, 24),
                        'capacity': 180,
                        'prices': {
                            'Emerald | 2-Bed Cabin': 4499,
                            'Ruby | 2-Bed Cabin': 4999,
                            'Diamond | 2-Bed Cabin': 5399,
                            'Diamond | Junior Suite': 6699, 
                        }
                    },
                ]
            },
            {
                'name': 'Cities in the Netherlands and Belgium',
                'description': 'Explore the heart of Europe along the beautiful Danube.',
                'cruise_type': 'Rivers',
                'company': 'Viva Cruises',
                'brand': 'Fluss.lu',
                'image_url': 'https://cdn.viva-cruises.com/image/crop/1366x1024/52eb4b1a-e616-4b5e-a0e8-7e61955529e2/auszeit-in-amsterdam.jpeg',
                'sessions': [
                    {
                        'start_date': date(2025, 8, 6),
                        'end_date': date(2025, 8, 13),
                        'capacity': 180,
                        'prices': {
                            'Emerald | 2-Bed Cabin': 2199,
                            'Ruby | 2-Bed Cabin': 2999,
                            'Diamond | 2-Bed Cabin': 3199,
                            'Diamond | Junior Suite': 3799, 
                        }
                    },
                ]
            }
        ]

        for cruise_data in cruises_data:
            cruise_type = CruiseType.objects.get(name=cruise_data['cruise_type'])
            company = CruiseCompany.objects.get(name=cruise_data['company'])
            brand = Brand.objects.get(name=cruise_data['brand'])

            cruise, created = Cruise.objects.update_or_create(
                name=cruise_data['name'],
                defaults={
                    'description': cruise_data['description'],
                    'cruise_type': cruise_type,
                    'company': company,
                    'brand': brand,
                    'image_url': cruise_data['image_url'],
                }
            )

            if created:
                self.stdout.write(f'Created cruise: {cruise.name}')
            else:
                self.stdout.write(f'Updated cruise: {cruise.name}')

            for session_data in cruise_data['sessions']:
                session, session_created = CruiseSession.objects.update_or_create(
                    cruise=cruise,
                    start_date=session_data['start_date'],
                    end_date=session_data['end_date'],
                    defaults={'capacity': session_data['capacity']}
                )

                for cabin_name, price in session_data['prices'].items():
                    cabin_type = CabinType.objects.get(name=cabin_name)
                    self.create_or_update_cruise_cabin_price(cruise, cabin_type, Decimal(price), session)

                if session_created:
                    self.stdout.write(f'Created session for {cruise.name}: {session.start_date} to {session.end_date}')
                else:
                    self.stdout.write(f'Updated session for {cruise.name}: {session.start_date} to {session.end_date}')
