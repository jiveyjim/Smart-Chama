from django.shortcuts import render, redirect
from django.http import HttpResponse

def signup(request):
    return render(request, 'signup.html')
def login(request):
    return render(request, 'login.html')
def forget_password(request):
    return render(request, 'forget password.html')