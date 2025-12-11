from django.shortcuts import render, redirect
from .forms import MemberForm
from django.contrib import messages
from django.contrib.auth.hashers import make_password,check_password
from .models import ChamaMember,Payments
from. import mpesa
from .forms import PaymentForm
import requests, base64, datetime,json,os
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse,HttpResponseBadRequest
from dotenv import load_dotenv
import uuid
from django.core.mail import send_mail
from django.conf import settings
from django.utils.timezone import now, timedelta
from django.db.models import Q 
from django.contrib.auth.models import User


load_dotenv()
MPESA_CONSUMER_KEY = os.getenv('MPESA_CONSUMER_KEY')
MPESA_CONSUMER_SECRET = os.getenv('MPESA_CONSUMER_SECRET')  
MPESA_SHORTCODE = os.getenv('MPESA_SHORTCODE')
MPESA_PASSKEY = os.getenv('MPESA_PASSKEY')
MPESA_ENVIRONMENT = os.getenv('MPESA_ENVIRONMENT')  # 'sandbox' or 'production'
MPESA_CALLBACK_URL = os.getenv('MPESA_CALLBACK_URL')
MPESA_BASE_URL= os.getenv('MPESA_BASE_URL')

# --------------------------
# SIGN UP (REGISTRATION)
# --------------------------

def signup(request):
    if request.method == 'POST':
        form = MemberForm(request.POST)
        if form.is_valid():
            member = form.save(commit=False)
            member.password = make_password(form.cleaned_data['password'])
            member.save()
            return redirect('login')
    else:
        form = MemberForm()
    return render(request, 'signup.html', {'form': form})
   

def login(request):
    if request.method == 'POST':
        identifier = request.POST.get('identifier')  # Email or phone
        password = request.POST.get('password')

        if not identifier or not password:
            messages.error(request, "Please enter both email/phone and password.")
            return render(request, 'login.html')

        # Prevent admin email from logging in here
        if User.objects.filter(email=identifier, is_staff=True).exists():
            messages.error(request, "This email belongs to an admin. Please use the admin login page.")
            return render(request, 'login.html')

        # Try to find member by email or phone
        member = ChamaMember.objects.filter(
            Q(email=identifier) | Q(phone_number=identifier)
        ).first()

        if member:
            if check_password(password, member.password):
                # Save member info in session securely
                request.session['member_id'] = member.id
                request.session['member_name'] = member.full_name

                # Redirect to member dashboard
                return redirect('member_home')
            else:
                messages.error(request, "Incorrect password.")
        else:
            messages.error(request, "Email or phone number not found.")

    return render(request, 'login.html')



# --------------------------
# LOGOUT
# --------------------------
def logout(request):
    request.session.flush()
    return redirect('login')



# --------------------------
# FORGOT PASSWORD (Page Only For Now)
# --------------------------
def forget_password(request):
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            member = ChamaMember.objects.get(email=email)
        except ChamaMember.DoesNotExist:
            messages.error(request, "This email is not registered.")
            return render(request, "forget_password.html")

        # Generate reset token
        token = str(uuid.uuid4())
        member.reset_token = token
        member.reset_token_expiry = now() + timedelta(hours=1)  # Valid 1 hour
        member.save() 

        # RESET LINK
        reset_link = request.build_absolute_uri(f"/reset_password/{token}/")

        # SEND EMAIL
        send_mail(
            subject="Smart Chama - Reset Your Password",
            message=f"Hello {member.full_name},\n\nClick the link below to reset your password:\n\n{reset_link}\n\nIf you did not request this, ignore this email.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[member.email],
        )

        messages.success(request, "A password reset link has been sent to your email.")
        return redirect("login")

    return render(request, "forget_password.html")


def reset_password(request, token):
    try:
        member = ChamaMember.objects.get(reset_token=token)
    except ChamaMember.DoesNotExist:
        messages.error(request, "Invalid or expired token.")
        return redirect("forget_password")

    # Check expiry
    if member.reset_token_expiry < now():
        messages.error(request, "This link has expired. Request a new reset link.")
        return redirect("forget_password")

    # If POST → Save new password
    if request.method == "POST":
        new_password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "reset_password.html")

        # Save new password
        member.password = make_password(new_password)
        member.reset_token = None
        member.reset_token_expiry = None
        member.save()

        messages.success(request, "Password reset successful. You can now log in.")
        return redirect("login")

    return render(request, "reset_password.html")




def member_home_page(request):
    member_id=request.session.get("member_id")

    if not member_id:
        return redirect('login') #if user is not logged in
    
    member=ChamaMember.objects.get(id=member_id)

    return render(request,'member_home.html',{'member':member})

def logout(request):
    request.session.flush() #this clears all session data
    return redirect('index')


def base(request):
    return render(request, 'base.html')

def deposit(request):
    if request.method=='POST':
        form= PaymentForm(request.POST)
        if form.is_valid():
            phone = mpesa.format_phone_number(form.cleaned_data['phone_number'])
            amount = int(form.cleaned_data['amount'])
            response=mpesa.initiate_stk_push(phone, amount)

            if response.get("ResponseCode") == "0":
                return render(request, 'pending.html', {'message': 'STK Push initiated successfully. Please check your phone.'})
            else:
                error_message = response.get("errorMessage", "An error occurred while initiating STK Push.")
                return render(request, 'payment.html', {'form': form, 'error': error_message})
    else:    
        form = PaymentForm()
    return render(request, 'deposit.html', {'form': form,})

def withdraw(request):
    return render(request, 'withdraw.html')

def index(request):
    return render(request, 'index.html')

def member_list(request):
    return render(request, 'member_list.html')

def statements(request):
    return render(request, 'statements.html')

def withdrawal_timeline(request):
    return render(request, 'withdrawal_timeline.html')

@csrf_exempt
def mpesa_callback(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Only POST requests are allowed") # Only allows POST requests

    try:
        # Parse the callback data from the request body
        callback_data = json.loads(request.body)
        
        # Check the result code
        result_code = callback_data["Body"]["stkCallback"]["ResultCode"]
        if result_code != 0:
            # Handle unsuccessful transaction
            error_message = callback_data["Body"]["stkCallback"]["ResultDesc"]
            return JsonResponse({"ResultCode": result_code, "ResultDesc": error_message})

        # Extract metadata from the callback
        checkout_id = callback_data["Body"]["stkCallback"]["CheckoutRequestID"]
        body = callback_data["Body"]["stkCallback"]["CallbackMetadata"]["Item"]

        # Find specific fields in the metadata
        amount = next(item["Value"] for item in body if item["Name"] == "Amount")
        mpesa_code = next(item["Value"] for item in body if item["Name"] == "MpesaReceiptNumber")
        phone = next(item["Value"] for item in body if item["Name"] == "PhoneNumber")

        # Save transaction to the database
        Payments.objects.create(
            amount=amount,
            checkout_id=checkout_id,
            mpesa_code=mpesa_code,
            phone_number=phone,
            status="Success"
        )
        
        # Return a success response to M-Pesa
        return JsonResponse({"C2B_Acknowledge": "Success"}, safe=False)

    except (json.JSONDecodeError, KeyError) as e:
        # Handle errors gracefully
        return HttpResponseBadRequest(f"Invalid request data: {str(e)}")

@csrf_exempt
def query_stk_push(checkout_request_id): #
    try:
        token = mpesa.generate_access_token() #
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"} #

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S') #
        # Password is Base64(Shortcode + Passkey + Timestamp)
        password = base64.b64encode(
            (MPESA_SHORTCODE + MPESA_PASSKEY + timestamp).encode() #
        ).decode() #

        request_body = {
            "BusinessShortCode": MPESA_SHORTCODE, #
            "Password": password, #
            "Timestamp": timestamp, #
            "CheckoutRequestID": checkout_request_id #
        }

        response = requests.post(
            f"{MPESA_BASE_URL}/mpesa/stkpushquery/v1/query", #
            json=request_body,
            headers=headers,
        ) #

        print(response.json()) #
        return response.json() #

    except requests.RequestException as e:
        print(f"Error querying STK status: {str(e)}") #
        return {"error": str(e)} #
    
def stk_status_view(request):
    if request.method == 'POST':
        try:
            # Parse the JSON body
            data = json.loads(request.body)
            checkout_request_id = data.get('checkout_request_id')

            # Query the STK push status using your backend function
            status = query_stk_push(checkout_request_id)

            # Return the status as a JSON response
            return JsonResponse({"status": status})
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON body"}, status=400)
