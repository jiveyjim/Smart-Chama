import requests,base64,os,datetime,os,re,json
from dotenv import load_dotenv
load_dotenv()

MPESA_CONSUMER_KEY = os.getenv('MPESA_CONSUMER_KEY')
MPESA_CONSUMER_SECRET = os.getenv('MPESA_CONSUMER_SECRET')  
MPESA_SHORTCODE = os.getenv('MPESA_SHORTCODE')
MPESA_PASSKEY = os.getenv('MPESA_PASSKEY')
MPESA_ENVIRONMENT = os.getenv('MPESA_ENVIRONMENT')  # 'sandbox' or 'production'
MPESA_CALLBACK_URL = os.getenv('MPESA_CALLBACK_URL')
MPESA_BASE_URL= os.getenv('MPESA_BASE_URL')


def generate_access_token():
    try:
        # 1. Base64 Encode Credentials
        credentials = f"{MPESA_CONSUMER_KEY}:{MPESA_CONSUMER_SECRET}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        # 2. Define Request Headers
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
        }

        # 3. Send GET Request to Token Endpoint
        response = requests.get(
            f"{MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials",
            headers=headers,
        ).json()

        # 4. Process Response
        if "access_token" in response:
            return response["access_token"]
        else:
            raise Exception("Access token missing in response.")

    # 5. Handle Connection Errors
    except requests.RequestException as e:
        raise Exception(f"Failed to connect to M-Pesa: {str(e)}")
    

def initiate_stk_push(phone, amount):
    try:
        # 1. Get Access Token
        token = generate_access_token()

        # 2. Define Request Headers using Bearer Token
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        # 3. Prepare Security Credentials (STK Password)
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        # The STK password is calculated by Base64 encoding the concatenation of
        # Shortcode, Passkey, and Timestamp.
        stk_password = base64.b64encode(
            (MPESA_SHORTCODE + MPESA_PASSKEY + timestamp).encode()
        ).decode()

        # 4. Construct the Request Body (Payload)
        request_body = {
            "BusinessShortCode": MPESA_SHORTCODE,
            "Password": stk_password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline", # Used for Lipa na M-Pesa
            "Amount": amount,
            "PartyA": phone, # The customer's phone number
            "PartyB": MPESA_SHORTCODE, # The merchant's shortcode
            "PhoneNumber": phone, # Same as PartyA
            "CallBackURL": MPESA_CALLBACK_URL, # Endpoint M-Pesa calls after transaction
            "AccountReference": "account", # Your internal account reference
            "TransactionDesc": "Payment for goods",
        }

        # 5. Send POST Request to the STK Push Endpoint
        response = requests.post(
            f"{MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest",
            json=request_body,
            headers=headers,
        ).json()

        return response

    except Exception as e:
        # Handle exceptions from token generation or request failure
        print(f"STK Push failed: {e}")
        return {"error": str(e)}


def format_phone_number(phone):
    phone = phone.replace("+", "")
    if re.match(r"^254\d{9}$", phone):
        return phone
    elif phone.startswith("0") and len(phone) == 10:
        return "254" + phone[1:]
    else:
        raise ValueError("Invalid phone number format")