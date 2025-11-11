"""Test settings for the Django application."""
import os

from p7 import settings as p7_settings

SECRET_KEY = "bogus"

INSTALLED_APPS = [
    "repository",
    "pgcrypto",
    "django_q",
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
Q_CLUSTER = p7_settings.Q_CLUSTER.copy()
Q_CLUSTER['sync'] = True
# DJANGO_Q database config. Docs: https://django-q2.readthedocs.io/en/master/configure.html

USE_PGCRYPTO = False
PGCRYPTO_KEY = None
