"""Configuration for the repository app."""
from django.apps import AppConfig

class RepositoryConfig(AppConfig):
    """Configuration for the repository app.
    
    params:
        AppConfig (django.apps): Base class for configuring a Django app.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "repository"
