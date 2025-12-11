import os
import base64
import datetime
import requests
import re
from dotenv import load_dotenv

from django.conf import settings

load_dotenv()

MPESA_BASE_URL = os.getenv('MPESA_BASE_URL')  # should be https://sandbox.safaricom.co.ke
MPESA_SHORTCODE = os.getenv('MPESA_SHORTCODE')
MPESA_PASSKEY = os.getenv('MPESA_PASSKEY')
MPESA_CONSUMER_KEY = os.getenv('MPESA_CONSUMER_KEY')
MPESA_CONSUMER_SECRET = os.getenv('MPESA_CONSUMER_SECRET')
MPESA_CALLBACK_URL = os.getenv('MPESA_CALLBACK_URL')

def generate_access_token():
    """Get OAuth token from Daraja (sandbox)."""
    auth = (MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET)
    url = f"{MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    resp = requests.get(url, auth=auth, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data.get("access_token")

def initiate_stk_push(phone, amount, account_reference="SmartChama", transaction_desc="Contribution"):
    """
    Initiate STK push. Returns response dict from Daraja.
    phone must be in format 2547XXXXXXXX
    """
    token = generate_access_token()
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode(f"{MPESA_SHORTCODE}{MPESA_PASSKEY}{timestamp}".encode()).decode()

    print("STK Push URL:", stk_push_url)


    payload = {
        "BusinessShortCode": MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone,
        "PartyB": MPESA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": MPESA_CALLBACK_URL,
        "AccountReference": account_reference,
        "TransactionDesc": transaction_desc
    }

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest"
    resp = requests.post(url, json=payload, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json()

def format_phone_number(phone):
    phone = phone.strip().replace("+", "").replace(" ", "")
    # Accept 07XXXXXXXX or 2547XXXXXXXX
    if re.match(r"^2547\d{8}$", phone):
        return phone
    if re.match(r"^07\d{8}$", phone):
        return "254" + phone[1:]
    raise ValueError("Invalid phone number format (use 07XXXXXXXX or +2547XXXXXXXX).")
