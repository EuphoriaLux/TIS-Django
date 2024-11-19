# cruises/management/commands/update_cruise_data.py

from django.core.management.base import BaseCommand
from django.db.models import signals
from cruises.signals import create_initial_data

class Command(BaseCommand):
    help = 'Updates cruise data by triggering the post_migrate signal'

    def handle(self, *args, **options):
        # Manually trigger the signal
        signals.post_migrate.send(
            sender=self.get_app_config('cruises'),
            app_config=self.get_app_config('cruises'),
            verbosity=2,
            interactive=False,
            using='default'
        )

    def get_app_config(self, app_label):
        from django.apps import apps
        return apps.get_app_config(app_label)