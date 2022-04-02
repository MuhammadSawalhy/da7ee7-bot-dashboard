from django.db import models

# Create your models here.

class Bot(models.Model):
    username = models.CharField(max_length=20, unique=True)
    token = models.CharField(max_length=100, unique=True)
