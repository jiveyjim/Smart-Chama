from django.urls import path, include
from adminapp import views
from adminapp import views

urlpatterns = [
    path('admin_announcement/',views.admin_announcement,name='admin_announcement'),
    path('admin_email/',views.admin_email,name='admin_email'),
    path('admin_home/',views.admin_home,name='admin_home'),
    path('admin_login/',views.admin_login,name='admin_login'),
    path('admin_members/',views.admin_members,name='admin_members'),
    path('admin_logout/',views.admin_logout,name='admin_logout'),
    path('admin/withdrawals/', views.admin_withdrawals, name='admin_withdrawals'),
    
]