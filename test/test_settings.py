"""Test settings for the Django application."""
import os

SECRET_KEY = "bogus"

INSTALLED_APPS = [
    "repository",
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

# DJANGO_Q database config. Docs: https://django-q2.readthedocs.io/en/master/configure.html
Q_CLUSTER = {
    'name': 'default',
    'retry': 3600,
    'timeout': 600,
    'recycle': 250,
    'save_limit': 10,
    'queue_limit': 100,
    'cpu_affinity': 1,
    'label': 'Django Q2',
    'orm': 'default',
}
