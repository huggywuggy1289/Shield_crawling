from django.db import models

class Hosts(models.Model):
    host = models.URLField(unique=True)
    redirect = models.URLField(null=True, blank=True)
    classification = models.CharField(max_length=255, null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    last_check_time = models.DateTimeField(null=True, blank=True)

class WordCount(models.Model):
    host = models.ForeignKey(Hosts, on_delete=models.CASCADE)
    words = models.CharField(max_length=255)
    count = models.IntegerField()

class FullSentence(models.Model):
    host = models.ForeignKey(Hosts, on_delete=models.CASCADE, related_name='full_sentences')
    full_sentence = models.TextField()

    def __str__(self):
        return f"{self.host} - {self.full_sentence}"

class Normal(models.Model):
    word = models.CharField(max_length=255)

class Casino(models.Model):
    word = models.CharField(max_length=255)

class Adult(models.Model):
    word = models.CharField(max_length=255)

class Copyright(models.Model):
    word = models.CharField(max_length=255)

class Whitelist(models.Model):
    url = models.URLField(unique=True)
