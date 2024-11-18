from django.apps import AppConfig


class CruisesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cruises'

    def ready(self):
        import cruises.signals  # Import the signals module