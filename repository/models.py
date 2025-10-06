# The model we use for our database
from django.db import models

class User(models.Model):
    # No extra fields; default "id" primary key is used (SERIAL)
    class Meta:
        db_table = '"users"'

class Service(models.Model):
    userId = models.ForeignKey(User, on_delete=models.CASCADE, db_column='userId')
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
    serviceId = models.ForeignKey(Service, on_delete=models.CASCADE, db_column='serviceId')
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
            models.UniqueConstraint(fields=['serviceId', 'serviceFileId'], name='uq_service_file_id'),
        ]

class Term(models.Model):
    termName = models.TextField()
    documentFrequency = models.BigIntegerField()

    class Meta:
        db_table = '"term"'

class InvertedIndex(models.Model):
    userId = models.ForeignKey(User, on_delete=models.CASCADE, db_column='userId')
    termId = models.ForeignKey(Term, on_delete=models.CASCADE, db_column='termId')

    class Meta:
        db_table = '"invertedindex"'
        constraints = [
            models.UniqueConstraint(fields=['userId', 'termId'], name='uq_inv_user_term'),
        ]

class Posting(models.Model):
    termId = models.ForeignKey(Term, on_delete=models.CASCADE, db_column='termId')
    fileId = models.ForeignKey(File, on_delete=models.CASCADE, db_column='fileId')
    termFrequency = models.BigIntegerField()

    class Meta:
        db_table = '"posting"'