from django.shortcuts import render, redirect
from django.http import HttpResponse

def signup(request):
    return render(request, 'signup.html')