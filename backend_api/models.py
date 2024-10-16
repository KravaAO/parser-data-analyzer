from django.db import models

# Create your models here.
class Youtube(models.Model):
    title = models.CharField(max_length=255)
    channel = models.CharField(max_length=255)
