"""Defines the database models for users, services, files, terms, inverted index, and postings."""

from django.db import models
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector, SearchVectorField

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
    oauthType = models.TextField()
    oauthToken = models.TextField()
    accessToken = models.TextField()
    accessTokenExpiration = models.DateTimeField()
    refreshToken = models.TextField()
    name = models.TextField()
    accountId = models.TextField()
    email = models.TextField()
    scopeName = models.TextField()

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
    serviceFileId = models.TextField()
    name = models.TextField()
    extension = models.TextField()
    downloadable = models.BooleanField()
    path = models.TextField()
    link = models.TextField()
    size = models.BigIntegerField()
    createdAt = models.DateTimeField()
    modifiedAt = models.DateTimeField()
    lastIndexed = models.DateTimeField(null=True, blank=True)
    snippet = models.TextField(null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    ts = models.GeneratedField(
        expression=(
            SearchVector('name',   weight='A', config='simple') +
            SearchVector('content', weight='B', config='english')
        ),
        output_field=SearchVectorField(),
        db_persist=True,
        editable=False,
        null=True,
    )

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


class Term(models.Model):
    """A class representing a unique term used in the inverted index.

    params:
        models (django.db): Base class for all models in Django.
    """

    # Natural key used by FKs in other tables
    termName = models.TextField(unique=True)

    class Meta:
        """Class defining metadata for the Term model."""

        app_label = "repository"
        db_table = '"term"'


class InvertedIndex(models.Model):
    """A class representing the inverted index for terms and their document frequencies.

    params:
        models (django.db): Base class for all models in Django.
    """

    # Per-user term stats
    userId = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column="userId",
        related_name="inverted_terms",
    )
    termName = models.ForeignKey(
        Term,
        to_field="termName",  # reference Term.termName (unique field)
        on_delete=models.CASCADE,
        db_column="termName",
        related_name="user_inverted_rows",
    )
    documentFrequency = models.BigIntegerField()

    class Meta:
        """Class defining metadata for the InvertedIndex model."""

        app_label = "repository"
        db_table = '"invertedindex"'
        constraints = [
            models.UniqueConstraint(
                fields=["userId", "termName"],
                name="uq_inv_user_term_name",
            ),
        ]


class Posting(models.Model):
    """A class representing a posting in the inverted index, linking terms to files.

    params:
        models (django.db): Base class for all models in Django.
    """

    termName = models.ForeignKey(
        Term,
        to_field="termName",  # reference Term.termName (unique field)
        on_delete=models.CASCADE,
        db_column="termName",
        related_name="postings",
    )
    fileId = models.ForeignKey(
        File,
        on_delete=models.CASCADE,
        db_column="fileId",
        related_name="postings",
    )
    termFrequency = models.BigIntegerField()

    class Meta:
        """Class defining metadata for the Posting model."""

        app_label = "repository"
        db_table = '"posting"'
        constraints = [
            models.UniqueConstraint(
                fields=["termName", "fileId"],
                name="uq_term_name_file_id",
            ),
        ]
