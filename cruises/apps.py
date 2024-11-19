# cruises/apps.py
from django.apps import AppConfig
from django.db.models.signals import post_migrate

class CruisesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cruises'

    def ready(self):
        from django.apps import apps
        from django.db import connection

        def populate_initial_data(sender, **kwargs):
            try:
                # Check if tables exist
                with connection.cursor() as cursor:
                    tables = connection.introspection.table_names()
                    if 'cruises_region' not in tables:
                        return

                # Check if data already exists
                Region = apps.get_model('cruises', 'Region')
                if Region.objects.exists():
                    return

                # Import your create_initial_data function
                from .signals import create_initial_data
                create_initial_data(sender, **kwargs)

            except Exception as e:
                print(f"Error in populate_initial_data: {e}")

        post_migrate.connect(populate_initial_data, sender=self)