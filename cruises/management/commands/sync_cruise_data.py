# cruises/management/commands/sync_cruise_data.py

from django.core.management.base import BaseCommand
from django.core import serializers
from django.apps import apps
from django.db import transaction, models
import json
import os
from pathlib import Path
from django.utils import timezone
from decimal import Decimal

class Command(BaseCommand):
    help = 'Load cruise fixtures with update capability'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def get_identifier_fields(self, model_name):
        """Define unique identifier fields for each model."""
        identifiers = {
            'region': ['name'],
            'port': ['name', 'country'],
            'cruisecompany': ['name'],
            'brand': ['name'],
            'ship': ['name', 'company'],
            'equipment': ['name'],
            'cabincategory': ['ship', 'category_code'],
            'cruisetype': ['name'],
            'cruise': ['name', 'ship'],
            'cruisesession': ['cruise', 'start_date', 'end_date'],
            'cruisesessioncabinprice': ['cruise_session', 'cabin_category']
        }
        return identifiers.get(model_name.lower(), ['id'])

    def process_decimal_field(self, value):
        """Convert string decimal values to Decimal objects"""
        if isinstance(value, str) and any(c.isdigit() for c in value):
            return Decimal(value.replace(',', '.'))
        return value

    def handle_relations(self, Model, fields):
        """Process related fields and return cleaned data"""
        cleaned_data = {}
        m2m_fields = {}

        for field_name, value in fields.items():
            field = Model._meta.get_field(field_name)
            
            if field.many_to_many:
                m2m_fields[field_name] = value
                continue
                
            if field.is_relation:
                if isinstance(value, int):
                    related_model = field.related_model
                    try:
                        cleaned_data[field_name] = related_model.objects.get(pk=value)
                    except related_model.DoesNotExist:
                        raise Exception(f"Related {field_name} with pk={value} does not exist")
                continue
                
            if isinstance(field, models.DecimalField):
                cleaned_data[field_name] = self.process_decimal_field(value)
                continue
                
            cleaned_data[field_name] = value
            
        return cleaned_data, m2m_fields

    def handle(self, *args, **options):
        fixtures_dir = Path('cruises/fixtures/initial')
        
        fixture_order = [
            '01_regions.json',
            '02_ports.json',
            '03_companies.json',
            '04_brands.json',
            '05_ships.json',
            '06_equipment.json',
            '07_cabin_categories.json',
            '08_cruise_types.json',
            '09_cruises.json',
            '10_cruise_sessions.json',
            '11_session_cabin_prices.json'
        ]

        stats = {
            'created': 0,
            'updated': 0,
            'skipped': 0
        }

        for fixture_file in fixture_order:
            fixture_path = fixtures_dir / fixture_file
            if not fixture_path.exists():
                self.stdout.write(f"Skipping {fixture_file} - file not found")
                continue

            self.stdout.write(f"\nProcessing {fixture_file}...")
            
            try:
                with open(fixture_path, 'r', encoding='utf-8') as f:
                    fixture_data = json.load(f)
            except json.JSONDecodeError as e:
                self.stderr.write(f"Error reading {fixture_file}: {str(e)}")
                continue

            for item in fixture_data:
                try:
                    with transaction.atomic():
                        model_name = item['model'].split('.')[-1]
                        Model = apps.get_model('cruises', model_name)

                        # Process fields and extract M2M relationships
                        cleaned_data, m2m_fields = self.handle_relations(Model, item['fields'])

                        # Try to get existing instance by PK or natural key
                        instance = None
                        if 'pk' in item:
                            try:
                                instance = Model.objects.get(pk=item['pk'])
                            except Model.DoesNotExist:
                                pass

                        if not instance:
                            identifier_fields = self.get_identifier_fields(model_name)
                            identifier_data = {
                                field: cleaned_data.get(field)
                                for field in identifier_fields
                                if field in cleaned_data
                            }
                            instance = Model.objects.filter(**identifier_data).first()

                        if instance and not options['dry_run']:
                            # Update existing record
                            for field, value in cleaned_data.items():
                                if field not in ['created_at', 'updated_at']:
                                    setattr(instance, field, value)
                            
                            instance.save()
                            
                            # Handle M2M relationships
                            for field_name, values in m2m_fields.items():
                                m2m_field = getattr(instance, field_name)
                                m2m_field.set(values)

                            stats['updated'] += 1
                            self.stdout.write(f"Updated {model_name}: {instance}")

                        elif not options['dry_run']:
                            # Create new record
                            instance = Model.objects.create(**cleaned_data)
                            
                            # Handle M2M relationships
                            for field_name, values in m2m_fields.items():
                                m2m_field = getattr(instance, field_name)
                                m2m_field.set(values)

                            stats['created'] += 1
                            self.stdout.write(f"Created {model_name}: {instance}")

                except Exception as e:
                    self.stderr.write(f"Error processing {model_name}: {str(e)}")
                    if options.get('verbosity', 1) > 1:
                        import traceback
                        self.stderr.write(traceback.format_exc())
                    stats['skipped'] += 1
                    continue

        # Print summary
        summary = f"""
Fixture processing complete:
- Created: {stats['created']}
- Updated: {stats['updated']}
- Skipped: {stats['skipped']}
{'(DRY RUN - No changes made)' if options['dry_run'] else ''}
"""
        self.stdout.write(self.style.SUCCESS(summary))