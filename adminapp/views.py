from django.shortcuts import render,redirect

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
