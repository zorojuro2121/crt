from django.db import models

class savedata(models.Model):
    name = models.CharField(max_length=50)
    mpn = models.CharField(max_length=50)