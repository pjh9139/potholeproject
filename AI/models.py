from django.db import models


class PotholeAI(models.Model):
    idx = models.AutoField(primary_key=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    date = models.CharField(max_length=20, null=False)
    filename = models.CharField(max_length=100, null=False)
    ai = models.IntegerField(default=0)
    find = models.IntegerField(default=0)
    folder = models.CharField(max_length=30, default="")
    address = models.CharField(max_length=30, default="")