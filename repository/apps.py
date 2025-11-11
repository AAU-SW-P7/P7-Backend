"""Configuration for the repository app."""
import sys
from django.apps import AppConfig
from django.db import connection, OperationalError


class RepositoryConfig(AppConfig):
    """Configuration for the repository app.
    params:
        AppConfig (django.apps): Base class for configuring a Django app.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "repository"

    def ready(self):
            # Skip during migrations, tests, collectstatic, etc.
            if any(cmd in sys.argv for cmd in ("makemigrations", "migrate", "test", "collectstatic")):
                return

            # List of PostgreSQL extensions you want enabled
            extensions = ["pg_trgm", "pgcrypto"]

            try:
                with connection.cursor() as cursor:
                    for ext in extensions:
                        cursor.execute(f"CREATE EXTENSION IF NOT EXISTS {ext};")
            except (OperationalError, RuntimeError):
                # Database might not be available (e.g., during startup)
                return