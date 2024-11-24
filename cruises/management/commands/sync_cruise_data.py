# cruises/management/commands/sync_cruise_data.py

from django.core.management.base import BaseCommand
from django.core import serializers
from django.apps import apps
from django.db import transaction
import json
import os
from pathlib import Path
from django.utils import timezone

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
            'cruisesession': ['cruise', 'start_date', 'end_date']
        }
        return identifiers.get(model_name.lower(), ['id'])

    def handle(self, *args, **options):
        fixtures_dir = Path('cruises/fixtures/initial')
        
        # Processing order to respect foreign key relationships
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
            '10_cruise_sessions.json'
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
                        
                        # Get identifier fields for this model
                        identifier_fields = self.get_identifier_fields(model_name)
                        identifier_data = {
                            field: item['fields'].get(field) 
                            for field in identifier_fields 
                            if field in item['fields']
                        }

                        # Handle foreign key fields in identifier
                        for field in identifier_fields:
                            if field in item['fields'] and isinstance(item['fields'][field], int):
                                related_field = Model._meta.get_field(field)
                                if related_field.is_relation:
                                    identifier_data[field] = related_field.related_model.objects.get(
                                        pk=item['fields'][field]
                                    )

                        # Try to find existing record
                        existing = Model.objects.filter(**identifier_data).first()

                        if existing and not options['dry_run']:
                            # Update existing record
                            for field, value in item['fields'].items():
                                if field not in ['created_at', 'updated_at']:
                                    field_instance = Model._meta.get_field(field)
                                    
                                    if field_instance.is_relation:
                                        if field_instance.many_to_many:
                                            # Handle M2M relationships after save
                                            continue
                                        elif field_instance.many_to_one:
                                            # Handle foreign key
                                            related_model = field_instance.related_model
                                            value = related_model.objects.get(pk=value)
                                    
                                    setattr(existing, field, value)
                            
                            existing.updated_at = timezone.now()
                            existing.save()

                            # Handle M2M relationships
                            for field, value in item['fields'].items():
                                field_instance = Model._meta.get_field(field)
                                if field_instance.many_to_many:
                                    m2m_field = getattr(existing, field)
                                    m2m_field.set(value)

                            stats['updated'] += 1
                            self.stdout.write(f"Updated {model_name}: {identifier_data}")
                            
                        elif not options['dry_run']:
                            # Create new record
                            new_data = item['fields'].copy()
                            
                            # Handle foreign key relationships
                            for field, value in new_data.items():
                                field_instance = Model._meta.get_field(field)
                                if field_instance.is_relation and not field_instance.many_to_many:
                                    if isinstance(value, int):
                                        related_model = field_instance.related_model
                                        new_data[field] = related_model.objects.get(pk=value)

                            # Remove M2M fields from create data
                            m2m_fields = {}
                            for field in list(new_data.keys()):
                                field_instance = Model._meta.get_field(field)
                                if field_instance.many_to_many:
                                    m2m_fields[field] = new_data.pop(field)

                            instance = Model.objects.create(**new_data)

                            # Handle M2M relationships after create
                            for field, value in m2m_fields.items():
                                m2m_field = getattr(instance, field)
                                m2m_field.set(value)

                            stats['created'] += 1
                            self.stdout.write(f"Created {model_name}: {identifier_data}")
                        else:
                            # Dry run
                            action = "Would update" if existing else "Would create"
                            self.stdout.write(f"{action} {model_name}: {identifier_data}")
                            stats['skipped'] += 1

                except Exception as e:
                    self.stderr.write(f"Error processing {model_name}: {str(e)}")
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