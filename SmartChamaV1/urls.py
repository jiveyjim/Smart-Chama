from django.contrib import admin
from django.urls import path, include
from SmartChamaV1 import views

urlpatterns = [
    path('base/', views.base, name='base'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('forget password/',views.forget_password, name='forget password'),
    path('members/home/',views.member_home_page,name="member_home"),
    path('logout/',views.logout,name='logout'),
    path('deposit/',views.deposit,name='deposit'),
    path('withdraw/',views.withdraw,name='withdraw'),
    path('',views.index,name='index'),
    path('member_list/',views.member_list,name='member_list'),
    path('statements/',views.statements,name='statements'),
    path('withdrawal_timeline/', views.withdrawal_timeline, name='withdrawal_timeline'),
     path('callback/',views.mpesa_callback,name='mpesa_callback'),
    path('stk_status/',views.stk_status_view,name='stk_status'),
]
