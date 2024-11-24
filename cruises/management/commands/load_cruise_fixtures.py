from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.apps import apps
import os

class Command(BaseCommand):
    help = 'Load all cruise fixtures in the correct order'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reload fixtures even if data exists',
        )

    def handle(self, *args, **options):
        # Check if data exists
        CruiseSession = apps.get_model('cruises', 'CruiseSession')
        
        if CruiseSession.objects.exists() and not options['force']:
            self.stdout.write(self.style.WARNING('Data already exists. Use --force to reload.'))
            return

        # List of fixture files in order
        fixtures = [
            '01_regions',
            '02_ports',
            '03_companies',
            '04_brands',
            '05_ships',
            '06_equipment',
            '07_cabin_categories',
            '08_cruise_types',
            '09_cruises',
            '10_cruise_sessions'
        ]

        try:
            for fixture in fixtures:
                self.stdout.write(f'Loading fixture: {fixture}')
                call_command('loaddata', f'initial/{fixture}')
                
            self.stdout.write(self.style.SUCCESS('Successfully loaded all fixtures'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error loading fixtures: {str(e)}'))
            raise