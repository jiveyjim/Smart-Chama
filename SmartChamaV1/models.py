from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class ChamaMember(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, unique=True)
    idNumber = models.CharField(max_length=20, unique=True)
    joined_date = models.DateTimeField(auto_now_add=True)
    password = models.CharField(max_length=128)
    user=models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True)


    def __str__(self):
        return self.full_name