from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

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
    

class Payments(models.Model):
    member=models.ForeignKey(ChamaMember,on_delete=models.CASCADE)
    amount=models.IntegerField()
    phone_number=models.CharField(max_length=15)
    transaction_code = models.CharField(max_length=50, blank=True, null=True)
    checkout_request_id = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default="Pending")
    timestamp = models.DateTimeField(default=now)  

    def __str__(self):
        return f"{self.member.full_name} - {self.amount} KES"  