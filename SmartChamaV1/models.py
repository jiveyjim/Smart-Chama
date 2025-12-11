from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now, timedelta


# ---------------------------
# 1. MEMBER MODEL
# ---------------------------
# models.py

class ChamaMember(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, unique=True)
    idNumber = models.CharField(max_length=20, unique=True)
    joined_date = models.DateTimeField(auto_now_add=True)
    password = models.CharField(max_length=128)
    
    # FOREIGN KEY to Django user (optional)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    # RESET PASSWORD FIELDS
    reset_token = models.CharField(max_length=200, blank=True, null=True)
    reset_token_expiry = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.full_name




# ---------------------------
# 2. PAYMENTS MODEL (DEPOSITS)
# ---------------------------
class Payments(models.Model):
    member = models.ForeignKey(ChamaMember, on_delete=models.CASCADE)
    amount = models.FloatField()

    # M-PESA details
    phone_number = models.CharField(max_length=15)
    transaction_code = models.CharField(max_length=50, blank=True, null=True)
    checkout_request_id = models.CharField(max_length=100)

    status = models.CharField(max_length=20, default="Pending")   # Pending, Successful, Failed
    timestamp = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.member.full_name} - {self.amount} KES"



# ---------------------------
# 3. STATEMENT MODEL (ALL TRANSACTIONS)
# ---------------------------
class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ("Deposit", "Deposit"),
        ("Withdrawal", "Withdrawal"),
    )

    member = models.ForeignKey(ChamaMember, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)

    amount = models.FloatField()
    mpesa_ref = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    date = models.DateTimeField(default=now)
    balance_after = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.member.full_name} - {self.type} - {self.amount}"



# ---------------------------
# 4. WITHDRAWAL REQUEST MODEL
# ---------------------------
class WithdrawalRequest(models.Model):
    STATUS_CHOICES = (
        ("PENDING", "PENDING"),
        ("APPROVED", "APPROVED"),
        ("DECLINED", "DECLINED"),
    )

    member = models.ForeignKey(ChamaMember, on_delete=models.CASCADE)
    amount = models.FloatField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    request_date = models.DateTimeField(auto_now_add=True)
    decision_date = models.DateTimeField(blank=True, null=True)

    admin_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.member.full_name} - {self.amount} KES - {self.status}"
