"""Test settings for the Django application."""
from math import ceil, floor
import multiprocessing
import os

from p7 import settings as p7_settings

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
Q_CLUSTER = p7_settings.Q_CLUSTER.copy()
# DJANGO_Q database config. Docs: https://django-q2.readthedocs.io/en/master/configure.html
# Q_CLUSTER = {
#     'name': 'default',
#     'workers': multiprocessing.cpu_count(),
#     'retry': 3600,
#     'timeout': 600,
#     'recycle': 250,
#     'save_limit': 10,
#     'queue_limit': 100,
#     'cpu_affinity': 1,
#     'label': 'Django Q2',
#     'orm': 'default',
#     'ALT_CLUSTERS':{
#         'low': {
#             'workers': ceil(multiprocessing.cpu_count()*0.25),
#         },
#         'high': {
#             'workers': floor(multiprocessing.cpu_count()*0.75),
#         },
#    }
# }
