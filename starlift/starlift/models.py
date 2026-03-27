from django.db import models

class Speaker(models.Model):
    name = models.CharField(max_length=200)
    sub = models.CharField(max_length=200)
    stack = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    status = models.CharField(max_length=50)
    nps = models.DecimalField(max_digits=4, decimal_places=1)
    img = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Event(models.Model):
    speaker = models.ForeignKey(Speaker, related_name='events', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=50) # 'past' or 'future'

    def __str__(self):
        return f"{self.title} ({self.status})"
