# yourapp/management/commands/populate_db.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from cruises.models import CruiseCompany, CruiseType, Brand, Cruise, CruiseSession, Equipment, CruiseCabinPrice,CabinType
from django.contrib.auth.models import User
from django.core.files import File
from django.conf import settings
import os
from decimal import Decimal

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

        # Create or update cruise categories

        self.create_or_update_cabin_type(
            name='Ruby | 2-Bed Cabin',
            description='Luxurious 16 m² cabin on the Ruby Deck. Equipped with two single beds or one double bed, a large panoramic window (non-opening), and all VIVA All-Inclusive amenities. Ideal for couples or friends who appreciate comfort and scenic views.',
            capacity=2,
            deck='Ruby'
        )
        
        
        self.create_or_update_cabin_type(
            name='Ruby | 2-Bed Cabin Rear',
            description='Spacious 16 m² cabin at the rear of the Ruby Deck. Offers a quiet location with a panoramic rear view, two single beds or one double bed, and all VIVA All-Inclusive services. Perfect for guests desiring a unique perspective and a bit more privacy.',
            capacity=2,
            deck='Ruby'
        )
        
        self.create_or_update_cabin_type(
            name='Diamond | 2-Bed Cabin',
            description='Exclusive 16 m² cabin on the Diamond Deck, the highest passenger deck. Enjoy superior views through the large panoramic window (non-opening), two single beds or one double bed, and all VIVA All-Inclusive offerings. Ideal for guests who prioritize a prime location.',
            capacity=2,
            deck='Diamond'
        )
        
        self.create_or_update_cabin_type(
            name='Emerald | 2-Bed Cabin',
            description='Comfortable 16 m² cabin on the Emerald Deck. Furnished with two single beds or one double bed, a large window (non-opening), and all VIVA All-Inclusive amenities. An excellent choice for guests seeking a good balance between location and price.',
            capacity=2,
            deck='Emerald'
        )
        
        self.create_or_update_cabin_type(
            name='Diamond | Suite',
            description='Generous 24 m² suite on the exclusive Diamond Deck. Enjoy luxurious space, a separate living room, a bedroom with a double bed, a large panoramic window (non-opening), and all VIVA All-Inclusive Premium services. The perfect choice for guests desiring the utmost comfort and exclusivity.',
            capacity=2,
            deck='Diamond'
        )

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

        for item in equipment_list:
            self.create_or_update_equipment(*item)

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
        equipment, created = Equipment.objects.get_or_create(
            name=name,  # 'name' field is for English names (standard)
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
            # Update all fields if the item already exists
            equipment.name_de = name_de
            equipment.name_fr = name_fr
            equipment.description = description
            equipment.description_de = description_de
            equipment.description_fr = description_fr
            equipment.save()
            self.stdout.write(f'Updated equipment: {name}')

        return equipment

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
    
    def create_or_update_cabin_type(self, name, description, capacity, deck, amenities=''):
        cabin_type, created = CabinType.objects.update_or_create(
            name=name,
            defaults={
                'description': description,
                'capacity': capacity,
                'deck': deck,
                'amenities': amenities
            }
        )
        if created:
            self.stdout.write(f'Created cabin type: {name}')
        else:
            self.stdout.write(f'Updated cabin type: {name}')