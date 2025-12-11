from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User

# ------------------ HELPER ------------------
def is_admin(user):
    """Check if the logged-in user is staff/admin."""
    return user.is_staff

# ------------------ ADMIN LOGIN ------------------
def admin_login(request):
    if request.method == 'POST':
        identifier = request.POST.get('identifier', '').strip()  # Email or username
        password = request.POST.get('password', '').strip()

        if not identifier or not password:
            messages.error(request, "Please enter both email/username and password.")
            return render(request, 'admin_login.html')

        # Try finding user by email first
        user_obj = None
        if '@' in identifier:
            user_obj = User.objects.filter(email=identifier, is_staff=True).first()
        if not user_obj:
            user_obj = User.objects.filter(username=identifier, is_staff=True).first()

        if user_obj:
            auth_user = authenticate(request, username=user_obj.username, password=password)
            if auth_user is not None and auth_user.is_staff:
                auth_login(request, auth_user)
                return redirect('admin_home')
            else:
                messages.error(request, "Incorrect password.")
        else:
            messages.error(request, "Admin not found or not authorized.")

    return render(request, 'admin_login.html')

# ------------------ ADMIN LOGOUT ------------------
@login_required
@user_passes_test(is_admin)
def admin_logout(request):
    auth_logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('index')

# ------------------ ADMIN DASHBOARD ------------------
@login_required
@user_passes_test(is_admin)
def admin_home(request):
    # Example: fetch all members, payments, announcements if needed
    return render(request, 'admin_home.html')

# ------------------ ADMIN MEMBERS PAGE ------------------
@login_required
@user_passes_test(is_admin)
def admin_members(request):
    # Fetch members to display
    from SmartChamaV1.models import ChamaMember  # Adjust app name if needed
    members = ChamaMember.objects.all()
    return render(request, 'admin_members.html', {'members': members})

# ------------------ ADMIN ANNOUNCEMENTS PAGE ------------------
@login_required
@user_passes_test(is_admin)
def admin_announcement(request):
    # Fetch announcements if needed
    return render(request, 'admin_announcement.html')

# ------------------ ADMIN EMAIL PAGE ------------------
@login_required
@user_passes_test(is_admin)
def admin_email(request):
    # Fetch email history or send email logic
    return render(request, 'admin_email.html')
