"""Defines the database models for users, services, files, terms, inverted index, and postings."""

from django.db import models
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
import pgcrypto
from repository.managers import FileManager



class User(models.Model):
    """A class representing a user of the application.

    params:
        models (django.db): Base class for all models in Django.
    """

    id = models.BigAutoField(primary_key=True)

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
    oauthType = pgcrypto.EncryptedTextField()
    oauthToken = pgcrypto.EncryptedTextField()
    accessToken = pgcrypto.EncryptedTextField()
    accessTokenExpiration = pgcrypto.EncryptedDateTimeField()
    refreshToken = pgcrypto.EncryptedTextField()
    name = pgcrypto.EncryptedTextField()
    accountId = pgcrypto.EncryptedTextField()
    email = pgcrypto.EncryptedTextField()
    scopeName = pgcrypto.EncryptedTextField()
    indexedAt = pgcrypto.EncryptedDateTimeField(null=True, blank=True)

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
    modifiedAt = pgcrypto.EncryptedDateTimeField()
    indexedAt = pgcrypto.EncryptedDateTimeField(null=True, blank=True)
    snippet = pgcrypto.EncryptedTextField(null=True, blank=True)
    content = pgcrypto.EncryptedTextField(null=True, blank=True)
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
