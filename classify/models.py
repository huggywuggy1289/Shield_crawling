from django.db import models

class Host(models.Model):
    host = models.URLField(unique=True)
    classification = models.CharField(max_length=255, null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    last_check_time = models.DateTimeField(null=True, blank=True)

class WordCount(models.Model):
    host = models.ForeignKey(Host, on_delete=models.CASCADE)
    redirect = models.URLField(null=True, blank=True)
    words = models.CharField(max_length=255)
    count = models.IntegerField()

class FullSentence(models.Model):
    host = models.ForeignKey(Host, on_delete=models.CASCADE, related_name='full_sentences')
    redirect = models.CharField(max_length=200, null=True, blank=True)
    full_sentence = models.TextField()

    def __str__(self):
        return f"{self.host} - {self.full_sentence}"
