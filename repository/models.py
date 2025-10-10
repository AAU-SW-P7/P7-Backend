# The model we use for our database
from django.db import models


class User(models.Model):
    id = models.BigAutoField(primary_key=True)

    class Meta:
        db_table = '"users"'


class Service(models.Model):
    id = models.BigAutoField(primary_key=True)
    userId = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='userId',
        related_name='services',
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
        db_table = '"service"'


class File(models.Model):
    id = models.BigAutoField(primary_key=True)
    serviceId = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        db_column='serviceId',
        related_name='files',
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

    class Meta:
        db_table = '"file"'
        constraints = [
            models.UniqueConstraint(
                fields=['serviceId', 'serviceFileId'],
                name='uq_service_file_id',
            ),
        ]


class Term(models.Model):
    # Natural key used by FKs in other tables
    termName = models.TextField(unique=True)

    class Meta:
        db_table = '"term"'


class InvertedIndex(models.Model):
    # Per-user term stats
    userId = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='userId',
        related_name='inverted_terms',
    )
    termName = models.ForeignKey(
        Term,
        to_field='termName',              # reference Term.termName (unique field)
        on_delete=models.CASCADE,
        db_column='termName',
        related_name='user_inverted_rows',
    )
    documentFrequency = models.BigIntegerField()

    class Meta:
        db_table = '"invertedindex"'
        constraints = [
            models.UniqueConstraint(
                fields=['userId', 'termName'],
                name='uq_inv_user_term_name',
            ),
        ]


class Posting(models.Model):
    termName = models.ForeignKey(
        Term,
        to_field='termName',              # reference Term.termName (unique field)
        on_delete=models.CASCADE,
        db_column='termName',
        related_name='postings',
    )
    fileId = models.ForeignKey(
        File,
        on_delete=models.CASCADE,
        db_column='fileId',
        related_name='postings',
    )
    termFrequency = models.BigIntegerField()

    class Meta:
        db_table = '"posting"'
        constraints = [
            models.UniqueConstraint(
                fields=['termName', 'fileId'],
                name='uq_term_name_file_id',
            ),
        ]