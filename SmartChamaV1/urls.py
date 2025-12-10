from django.contrib import admin
from django.urls import path, include
from SmartChamaV1 import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('forget password/',views.forget_password, name='forget password'),
    path('members/home/',views.member_home_page,name="member_home"),
    path('logout/',views.logout,name='logout'),
    path('admin_announcement/',views.admin_announcement,name='admin_announcement'),
    path('admin_email/',views.admin_email,name='admin_email'),
    path('admin_home/',views.admin_home,name='admin_home'),
    path('admin_login/',views.admin_login,name='admin_login'),
    path('admin_members/',views.admin_members,name='admin_members'),
    path('deposit/',views.deposit,name='deposit'),
    path('withdraw/',views.withdraw,name='withdraw'),
    path('',views.index,name='index'),
    path('member_list/',views.member_list,name='member_list'),
    path('statements/',views.statements,name='statements'),
    path('withdrawal_timeline/', views.withdrawal_timeline, name='withdrawal_timeline'),
]
