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
]
