from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import logout, authenticate, login
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth.forms import AuthenticationForm

def index(request):
    return render(request, 'base_login.html')

def register(request):
    if request.method == 'POST':
        alias = request.POST.get('alias')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if password != password2:
            messages.error(request, "Las contraseñas no coinciden.")
            return render(request, 'register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Ese correo ya está en uso.")
            return render(request, 'register.html')
        if User.objects.filter(username=alias).exists():
            messages.error(request, "Ese Alias ya está en uso.")
            return render(request, 'register.html')

        user = User.objects.create(
            username=alias,
            email=email,
            password=make_password(password)
        )
        user.save()
        messages.success(request, "Cuenta creada con éxito. ¡Ya puedes iniciar sesión!")        
        return redirect('register')
    return render(request, 'register.html')

def loggin(request):
    if request.method == 'POST':
        email = request.POST.get('username')  
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
        except User.DoesNotExist:
            user = None

        if user is not None:
            login(request, user)
            return redirect('user_profile')  
        else:
            messages.error(request, 'Correo o contraseña incorrectos.')
            response = render(request, 'login.html')
            response.status_code = 401  # <- en caso de fallo de login: Código de error 401
            return response
    return render(request, 'login.html')

def loggout(request):
    logout(request)
    return redirect('explore')


