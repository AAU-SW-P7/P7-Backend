import os

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