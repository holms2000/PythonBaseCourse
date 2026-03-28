# users/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import RegisterForm, LoginForm

def register_view(request):
    """
    Обработчик регистрации.
    """
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Автоматически логиним пользователя после регистрации
            login(request, user)
            return redirect('main_view') # Перенаправляем на главную страницу
    else:
        form = RegisterForm()
    
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    """
    Обработчик входа в систему.
    """
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('main_view')
    else:
        form = LoginForm()
    
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    """
    Обработчик выхода из системы.
    """
    logout(request)
    return redirect('login') # Перенаправляем на страницу входа

def profile_view(request):
    """
    Пример страницы профиля (можно расширить).
    """
    if not request.user.is_authenticated:
        return redirect('login')
        
    return render(request, 'users/profile.html', {'user': request.user})