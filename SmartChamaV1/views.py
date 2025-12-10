from django.shortcuts import render, redirect
from .forms import MemberForm
from django.contrib import messages
from django.contrib.auth.hashers import make_password,check_password
from .models import ChamaMember

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


<<<<<<< HEAD


=======
>>>>>>> recovered-work
def login(request):
    if request.method == 'POST':
        identifier = request.POST.get('identifier')  # Email or Phone Number
        password = request.POST.get('password')

        member = None

        # Try login with email
        try:
            member = ChamaMember.objects.get(email=identifier)
        except ChamaMember.DoesNotExist:
            pass

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


def admin_announcement(request):
    return render(request, 'admin_announcement.html')

def admin_email(request):
    return render(request, 'admin_email.html')

def base(request):
    return render(request, 'base.html')

def admin_home(request):
    return render(request, 'admin_home.html')

def admin_login(request):
    return render(request, 'admin_login.html')

def admin_members(request):
    return render(request, 'admin_members.html')

def deposit(request):
    return render(request, 'deposit.html')

def withdraw(request):
    return render(request, 'withdraw.html')

def index(request):
    return render(request, 'index.html')

def member_list(request):
    return render(request, 'member_list.html')

def statements(request):
    return render(request, 'statements.html')

def withdrawal_timeline(request):
<<<<<<< HEAD
    return render(request, 'withdrawal_timeline.html')
=======
    return render(request, 'withdrawal_timeline.html')
>>>>>>> recovered-work
