# quotes/apps.py
from django.apps import AppConfig

class QuotesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'quotes'  # This should match your folder name
    verbose_name = 'Quotes'  # This will be displayed in admin