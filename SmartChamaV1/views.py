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

load_dotenv()
MPESA_CONSUMER_KEY = os.getenv('MPESA_CONSUMER_KEY')
MPESA_CONSUMER_SECRET = os.getenv('MPESA_CONSUMER_SECRET')  
MPESA_SHORTCODE = os.getenv('MPESA_SHORTCODE')
MPESA_PASSKEY = os.getenv('MPESA_PASSKEY')
MPESA_ENVIRONMENT = os.getenv('MPESA_ENVIRONMENT')  # 'sandbox' or 'production'
MPESA_CALLBACK_URL = os.getenv('MPESA_CALLBACK_URL')
MPESA_BASE_URL= os.getenv('MPESA_BASE_URL')

def signup(request):
    if request.method=='POST':
        form =MemberForm(request.POST)
        if form.is_valid():
            member = form.save(commit=False)
            member.password= make_password(form.cleaned_data['password'])
            member.save()
            # messages.success(request, f'Acount created suessfully!')
            return redirect('login')
    else:
        form=MemberForm()  

    return render(request, 'signup.html',{'form':form})


def login(request):
    if request.method == 'POST':
        identifier = request.POST.get('identifier')  # Email or Phone Number
        password = request.POST.get('password')

        member = None

        # Try login with email
        try:
            member = ChamaMember.objects.get(email=identifier)
        except ChamaMember.DoesNotExist:
            member=None

        # If not found, try phone number
        if member is None:
            try:
                member = ChamaMember.objects.get(phone_number=identifier)
            except ChamaMember.DoesNotExist:
                member = None    

        if member:
            if check_password(password, member.password):
                request.session['member_id'] = member.id
                request.session['member_name'] = member.full_name
                return redirect('member_home')
            else:
                messages.error(request, "Incorrect password")
        else:
            messages.error(request, "Email or phone number not found")

    return render(request, 'login.html')

def forget_password(request):
    return render(request, 'forget password.html')


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
