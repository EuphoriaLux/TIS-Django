# cruises/apps.py
from django.apps import AppConfig
from django.db.models.signals import post_migrate

class CruisesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cruises'

    def ready(self):
        from django.apps import apps
        from django.db import connection
