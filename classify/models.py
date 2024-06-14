from django.db import models

class Host(models.Model):
    host = models.URLField(unique=True)
    classification = models.CharField(max_length=255, null=True, blank=True)

class WordCount(models.Model):
    host = models.ForeignKey(Host, on_delete=models.CASCADE)
    redirect = models.URLField(null=True, blank=True)
    words = models.CharField(max_length=255)
    count = models.IntegerField()
