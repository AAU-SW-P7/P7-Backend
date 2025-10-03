# The model we use for our database
from django.db import models

class User(models.Model):
    username = models.TextField()
    primaryProvider = models.TextField()

    class Meta:
        db_table = '"users"'

class Service(models.Model):
    userid = models.ForeignKey(User, on_delete=models.CASCADE, db_column='userid')
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
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, db_column='parent')
    name = models.TextField()
    type = models.TextField()
    downloadable = models.BooleanField()
    path = models.TextField()
    link = models.TextField()
    createdAt = models.DateTimeField()
    lastIndexed = models.DateTimeField()
    checksum = models.TextField(null=True, blank=True)
    snippet = models.TextField(null=True, blank=True)

    class Meta:
        db_table = '"file"'

class Term(models.Model):
    termName = models.TextField()
    documentFrequency = models.IntegerField()

    class Meta:
        db_table = '"term"'

class InvertedIndex(models.Model):
    userId = models.ForeignKey(User, on_delete=models.CASCADE, db_column='userId')
    termId = models.ForeignKey(Term, on_delete=models.CASCADE, db_column='termId')

    class Meta:
        db_table = '"invertedindex"'
        # If you add a unique pair at the DB level, reflect it here:
        # unique_together = (('userId', 'termId'),)

class Posting(models.Model):
    termId = models.ForeignKey(Term, on_delete=models.CASCADE, db_column='termId')
    fileId = models.ForeignKey(File, on_delete=models.CASCADE, db_column='fileId')
    termFrequency = models.IntegerField()

    class Meta:
        db_table = '"posting"'