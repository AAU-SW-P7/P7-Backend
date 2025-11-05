"""Defines the database models for users, services, files, terms, inverted index, and postings."""

from django.db import models, connection
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField

from repository.managers import FileManager
import pgcrypto


class User(models.Model):
    """A class representing a user of the application.

    params:
        models (django.db): Base class for all models in Django.
    """

    id = models.BigAutoField(primary_key=True)
    salt = models.TextField()

    def generate_salt(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT gen_salt('bf')")
            self.salt = cursor.fetchone()[0]

    class Meta:
        """Class defining metadata for the User model."""

        app_label = "repository"
        db_table = '"users"'


class Service(models.Model):
    """A class representing a service used by the application.

    params:
        models (django.db): Base class for all models in Django.
    """

    id = models.BigAutoField(primary_key=True)
    userId = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column="userId",
        related_name="services",
    )
    oauthType = models.TextField()
    oauthToken = models.TextField()
    accessToken = models.TextField()
    accessTokenExpiration = models.DateTimeField()
    refreshToken = models.TextField()
    name = models.TextField()
    accountId = models.TextField()
    email = models.TextField()
    scopeName = models.TextField()
    indexedAt = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Class defining metadata for the Service model."""

        app_label = "repository"
        db_table = '"service"'


class File(models.Model):
    """A class representing a file associated with a service.

    params:
        models (django.db): Base class for all models in Django.
    """
    objects = FileManager()
    id = models.BigAutoField(primary_key=True)
    serviceId = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        db_column="serviceId",
        related_name="files",
    )
    serviceFileId = pgcrypto.EncryptedTextField()
    name = pgcrypto.EncryptedTextField()
    extension = models.TextField()
    downloadable = models.BooleanField()
    path = pgcrypto.EncryptedTextField()
    link = pgcrypto.EncryptedTextField()
    size = models.BigIntegerField()
    createdAt = pgcrypto.EncryptedDateTimeField()
    modifiedAt = models.DateTimeField()
    indexedAt = models.DateTimeField(null=True, blank=True)
    snippet = models.TextField(null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    ts = SearchVectorField(null=True)

    class Meta:
        """Class defining metadata for the File model."""

        app_label = "repository"
        db_table = '"file"'
        constraints = [
            models.UniqueConstraint(
                fields=["serviceId", "serviceFileId"],
                name="uq_service_file_id",
            ),
        ]
        # GIN index over a weighted SearchVector expression
        indexes = [GinIndex(name="file_search_gin", fields=["ts"])]

