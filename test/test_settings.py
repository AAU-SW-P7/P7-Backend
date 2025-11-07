"""Test settings for the Django application."""
import os
SECRET_KEY = "test-secret-key"

INSTALLED_APPS = [
    "repository",
    "pgcrypto",
]

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DATABASE_ENGINE"),
        "NAME": os.getenv("DATABASE_NAME") + "_test",
        "USER": os.getenv("DATABASE_USERNAME"),
        "PASSWORD": os.getenv("DATABASE_PASSWORD"),
        "HOST": os.getenv("DATABASE_HOST"),
        "PORT": os.getenv("DATABASE_PORT"),
    }
}

USE_PGCRYPTO = False
PGCRYPTO_KEY = None