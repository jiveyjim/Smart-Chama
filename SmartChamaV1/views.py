from django.shortcuts import render, redirect
from django.http import HttpResponse

def signup(request):
    return render(request, 'signup.html')

def login(request):
    return render(request, 'login.html')

def forget_password(request):
    return render(request, 'forget password.html')

def base(request):
    return render(request, 'base.html')

def deposit(request):
    return render(request, 'deposit.html')

def index(request):
    return render(request, 'index.html')

def member_home(request):
    return render(request, 'member_home.html')

def member_list(crequest):
    return render(request, 'member_list.html')

def statements(request):
    return render(request, 'statements.html')

def withdraw(request):
    return render(request, 'withdraw.html')

def admin_announcement(request):
    return render(request, 'admin_announcement.html')

def admin_email(request):
    return render(request, 'admin_email.html')

def admin_home(request):
    return render(request, 'admin_home.html')

def admin_login(request):
    return render(request, 'admin_login.html')

def admin_members(request):
    return render(request, 'admin_members.html')

def signup(request):
    return render(request, 'signup.html')

def withdrawal_timeline(request):
    return render(request, 'withdrawal_timeline.html')
