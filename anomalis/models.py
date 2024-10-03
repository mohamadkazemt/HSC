from django.db import models

from accounts.forms import User


class Location(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Anomalytype(models.Model):
    type = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name



class Anomaly(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    anomalytype = models.ForeignKey(Anomalytype, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_anomalies')
    followup = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followup_anomalies')
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.description