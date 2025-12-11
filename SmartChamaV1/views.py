from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as dj_login
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
import uuid, os, json
from django.contrib.auth.models import User

from .models import ChamaMember, Payments, Transaction, WithdrawalRequest
from .forms import MemberForm, PaymentForm, WithdrawalForm
from . import mpesa
from dotenv import load_dotenv

load_dotenv()
MPESA_CONSUMER_KEY = os.getenv('MPESA_CONSUMER_KEY')
MPESA_CONSUMER_SECRET = os.getenv('MPESA_CONSUMER_SECRET')  
MPESA_SHORTCODE = os.getenv('MPESA_SHORTCODE')
MPESA_PASSKEY = os.getenv('MPESA_PASSKEY')
MPESA_ENVIRONMENT = os.getenv('MPESA_ENVIRONMENT')  # 'sandbox' or 'production'
MPESA_CALLBACK_URL = os.getenv('MPESA_CALLBACK_URL')
MPESA_BASE_URL= os.getenv('MPESA_BASE_URL')


# --------------------------
# HELPER: get logged member
# --------------------------
def base(request):
    return render(request, 'base.html')

def get_logged_member(request):
    member_id = request.session.get('member_id')
    if not member_id:
        return None
    try:
        return ChamaMember.objects.get(id=member_id)
    except ChamaMember.DoesNotExist:
        return None


# --------------------------
# SIGN UP
# --------------------------
def signup(request):
    if request.method == 'POST':
        form = MemberForm(request.POST)
        if form.is_valid():
            member = form.save(commit=False)
            member.password = make_password(form.cleaned_data['password'])
            member.save()
            messages.success(request, "Account created successfully. You can now log in.")
            return redirect('login')
    else:
        form = MemberForm()
    return render(request, 'signup.html', {'form': form})


# --------------------------
# LOGIN
# --------------------------
def login(request):
    if request.method == 'POST':
        identifier = request.POST.get('identifier')  # email or phone
        password = request.POST.get('password')

        if not identifier or not password:
            messages.error(request, "Please enter both email/phone and password.")
            return render(request, 'login.html')

        # Prevent admin email login here
        if User.objects.filter(email=identifier, is_staff=True).exists():
            messages.error(request, "This email belongs to an admin. Please use the admin login page.")
            return render(request, 'login.html')

        # Authenticate member via ChamaMember table
        member = ChamaMember.objects.filter(Q(email=identifier) | Q(phone_number=identifier)).first()
        if member and check_password(password, member.password):
            # Save member info in session
            request.session['member_id'] = member.id
            request.session['member_name'] = member.full_name
            return redirect('member_home')
        else:
            messages.error(request, "Invalid email/phone or password.")

    return render(request, 'login.html')


# --------------------------
# LOGOUT
# --------------------------
def logout(request):
    request.session.flush()
    return redirect('index')


# --------------------------
# FORGOT PASSWORD
# --------------------------
def forget_password(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            member = ChamaMember.objects.get(email=email)
        except ChamaMember.DoesNotExist:
            messages.error(request, "Email not registered.")
            return render(request, "forget_password.html")

        token = str(uuid.uuid4())
        member.reset_token = token
        member.reset_token_expiry = timezone.now() + timezone.timedelta(hours=1)
        member.save()

        reset_link = request.build_absolute_uri(f"/reset_password/{token}/")

        send_mail(
            subject="Smart Chama - Reset Your Password",
            message=f"Hello {member.full_name},\n\nClick to reset: {reset_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[member.email],
        )

        messages.success(request, "Password reset link sent to your email.")
        return redirect("login")

    return render(request, "forget_password.html")


# --------------------------
# RESET PASSWORD
# --------------------------
def reset_password(request, token):
    try:
        member = ChamaMember.objects.get(reset_token=token)
    except ChamaMember.DoesNotExist:
        messages.error(request, "Invalid or expired token.")
        return redirect("forget_password")

    if member.reset_token_expiry < timezone.now():
        messages.error(request, "Link expired. Request a new reset link.")
        return redirect("forget_password")

    if request.method == "POST":
        new_password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "reset_password.html")
        member.password = make_password(new_password)
        member.reset_token = None
        member.reset_token_expiry = None
        member.save()
        messages.success(request, "Password reset successful.")
        return redirect("login")

    return render(request, "reset_password.html")


# --------------------------
# MEMBER HOME
# --------------------------
def member_home_page(request):
    member = get_logged_member(request)
    if not member:
        return redirect('login')
    return render(request, 'member_home.html', {'member': member})


def deposit(request):
    member = get_logged_member(request)
    if not member:
        return redirect('login')

    recent_deposits = Payments.objects.filter(member=member).order_by('-timestamp')[:5]

    if request.method == 'POST':
        amount = request.POST.get('amount')
        method = request.POST.get('payment_method')
        phone = request.POST.get('phone_number')
        trx_id = request.POST.get('transaction_id')

        # Validate amount
        if not amount or float(amount) < 10:
            return render(request, 'deposit.html', {
                'member': member,
                'recent_deposits': recent_deposits,
                'error': 'Minimum deposit amount is KES 10.'
            })

        amount = float(amount)

        # Manual deposit
        if method == "manual":
            payment = Payments.objects.create(
                member=member,
                amount=amount,
                phone_number="N/A",
                transaction_code=trx_id if trx_id else None,
                checkout_request_id="MANUAL",
                status="Successful"
            )

            # Add transaction record
            last_balance = Transaction.objects.filter(member=member).order_by('-date').first()
            new_balance = (last_balance.balance_after if last_balance else 0) + amount

            Transaction.objects.create(
                member=member,
                type="Deposit",
                amount=amount,
                mpesa_ref=trx_id,
                balance_after=new_balance,
                notes="Manual deposit"
            )

            return render(request, 'deposit.html', {
                'member': member,
                'recent_deposits': recent_deposits,
                'success': 'Manual deposit recorded successfully.'
            })

        # MPESA STK push
        if method == "mpesa":
            if not phone:
                return render(request, 'deposit.html', {
                    'member': member,
                    'recent_deposits': recent_deposits,
                    'error': 'Phone number is required for M-PESA STK push.'
                })

            try:
                phone = mpesa.format_phone_number(phone)
                response = mpesa.initiate_stk_push(phone, int(amount))
            except Exception as e:
                return render(request, 'deposit.html', {
                    'member': member,
                    'recent_deposits': recent_deposits,
                    'error': f"STK push failed: {str(e)}"
                })

            if response.get("ResponseCode") == "0":
                Payments.objects.create(
                    member=member,
                    amount=amount,
                    phone_number=phone,
                    transaction_code=None,
                    checkout_request_id=response.get("CheckoutRequestID"),
                    status="Pending"
                )

                return render(request, 'deposit.html', {
                    'member': member,
                    'recent_deposits': recent_deposits,
                    'success': "STK Push sent. Check your phone."
                })

            return render(request, 'deposit.html', {
                'member': member,
                'recent_deposits': recent_deposits,
                'error': response.get("errorMessage", "Failed to initiate STK push.")
            })

    # GET request
    return render(request, 'deposit.html', {
        'member': member,
        'recent_deposits': recent_deposits
    })


# --------------------------
# MPESA CALLBACK
# --------------------------
@csrf_exempt
def mpesa_callback(request):
    try:
        body = request.body.decode('utf-8')
        data = json.loads(body)
    except:
        return HttpResponse(status=400)

    stk = data.get('Body', {}).get('stkCallback') or data.get('stkCallback')
    if not stk:
        return HttpResponse(status=200)

    result_code = stk.get('ResultCode')
    result_desc = stk.get('ResultDesc', '')
    checkout_request_id = stk.get('CheckoutRequestID') or stk.get('CheckoutRequestId')

    callback_metadata = stk.get('CallbackMetadata') or {}
    items = callback_metadata.get('Item') if callback_metadata else None

    mpesa_receipt = None
    amount = None
    mpesa_phone = None
    if items:
        for item in items:
            name = item.get('Name', '').lower()
            value = item.get('Value')
            if name in ('mpesanumber','mpesareceiptnumber','mpesa_receiptnumber'): mpesa_receipt = value
            if name == 'amount': amount = float(value)
            if name in ('phonenumber','phone'): mpesa_phone = str(value)

    payment = Payments.objects.filter(checkout_request_id__iexact=checkout_request_id).first()
    if not payment and mpesa_phone and amount:
        window = timezone.now() - timezone.timedelta(minutes=10)
        payment = Payments.objects.filter(phone_number__endswith=mpesa_phone[-9:], amount=amount, timestamp__gte=window).order_by('-timestamp').first()

    if result_code == 0 or str(result_code) == "0":
        if payment:
            with transaction.atomic():
                payment.status = "Successful"
                payment.transaction_code = mpesa_receipt or payment.transaction_code
                payment.timestamp = timezone.now()
                payment.save()
                member = payment.member
                member.balance = (member.balance or 0) + float(payment.amount)
                member.save()
                Transaction.objects.create(member=member, type="Deposit", amount=payment.amount,
                                           mpesa_ref=payment.transaction_code, notes=f"STK push confirmed: {result_desc}",
                                           date=timezone.now(), balance_after=member.balance)
    else:
        if payment:
            payment.status = "Failed"
            payment.transaction_code = mpesa_receipt or payment.transaction_code
            payment.timestamp = timezone.now()
            payment.save()

    return HttpResponse(status=200)


# --------------------------
# WITHDRAW REQUEST
# --------------------------
@login_required
def withdraw_request(request):
    member = get_logged_member(request)
    if not member:
        return redirect('login')

    if request.method == 'POST':
        form = WithdrawalForm(request.POST)
        if form.is_valid():
            amount = float(form.cleaned_data['amount'])
            notes = form.cleaned_data.get('notes', '')

            if amount > (member.balance or 0):
                messages.error(request, "Insufficient balance.")
                return render(request, 'withdraw.html', {'form': form, 'member': member})

            WithdrawalRequest.objects.create(member=member, amount=amount, status='PENDING', admin_notes=notes)
            messages.success(request, "Withdrawal request submitted.")
            return redirect('member_home')
    else:
        form = WithdrawalForm()

    return render(request, 'withdraw.html', {'form': form, 'member': member})


# --------------------------
# STATEMENTS
# --------------------------
@login_required
def statements(request):
    member = get_logged_member(request)
    if not member:
        return redirect('login')

    statements_qs = Transaction.objects.filter(member=member).order_by('-date')
    return render(request, 'statements.html', {'statements': statements_qs})


# --------------------------
# WITHDRAWAL TIMELINE
# --------------------------
@login_required
def withdrawal_timeline(request):
    member = get_logged_member(request)
    if not member:
        return redirect('login')

    timeline = WithdrawalRequest.objects.select_related('member').order_by('request_date')
    pending_first = timeline.filter(status='PENDING').order_by('request_date').first()

    for idx, entry in enumerate(timeline, start=1):
        entry.position = idx
        entry.is_current_turn = (entry == pending_first)

    return render(request, 'withdrawal_timeline.html', {'timeline': timeline, 'today': timezone.now()})


# --------------------------
# OTHER PAGES
# --------------------------
def withdraw(request):
    member = get_logged_member(request)
    if not member:
        return redirect('login')
    return render(request, 'withdraw.html', {'member': member})

def member_list(request):
    member = get_logged_member(request)
    if not member:
        return redirect('login')
    members = ChamaMember.objects.all()
    return render(request, 'member_list.html', {'members': members})

def index(request):
    return render(request, 'index.html')
