from django.db import models

class Speaker(models.Model):
    name = models.CharField(max_length=200)
    sub = models.CharField(max_length=200)
    stack = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    status = models.CharField(max_length=50)
    nps = models.DecimalField(max_digits=4, decimal_places=1)
    img = models.CharField(max_length=100)

    class Meta:
        db_table = 'starlift_speaker'

    def __str__(self):
        return self.name

class Event(models.Model):
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=50) # 'past' or 'future'
    date = models.CharField(max_length=100, null=True, blank=True)
    location = models.CharField(max_length=200, null=True, blank=True)
    link = models.CharField(max_length=500, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    schedule = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'starlift_event'

    def __str__(self):
        return f"{self.title} ({self.status})"
