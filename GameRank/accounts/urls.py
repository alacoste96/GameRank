from . import views
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LoginView

urlpatterns = [
    path('', views.loggin),
    path('login', views.loggin, name='login'),
    path('register', views.register, name='register'),
    path('logout', views.loggout, name='logout'),
]
