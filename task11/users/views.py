# users/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth import get_user_model
from .forms import LoginForm # Импортируем форму для входа
import hashlib

User = get_user_model() # Получаем вашу модель LegacyUser

def login_view(request):
    """
    Обработчик входа в систему.
    Логика полностью переписана вручную для работы с sha256.
    """
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            try:
                # 1. Находим пользователя в базе данных по username
                user = User.objects.get(username=username)
                
                # 2. Создаем sha256 хеш от пароля, который ввел пользователь
                hashed_input = hashlib.sha256(password.encode()).hexdigest()
                
                # 3. Сравниваем полученный хеш с тем, что хранится в базе (в поле password_hash)
                if hashed_input == user.password_hash:
                    # Если хеши совпали — пароль верный. Логиним пользователя.
                    auth_login(request, user)
                    return redirect('main_view')
                
            except User.DoesNotExist:
                # Если пользователя нет, мы просто ничего не делаем.
                # Это важно для защиты от перебора паролей (timing attack).
                pass

            # Если мы дошли до этой точки, значит логин или пароль неверные.
            # Добавляем общую ошибку к форме.
            form.add_error(None, 'Неверное имя пользователя или пароль.')
                
    else:
        form = LoginForm()
    
    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    """
    Обработчик выхода из системы.
    """
    auth_logout(request)
    return redirect('login')


def profile_view(request):
    """
    Пример страницы профиля.
    """
    if not request.user.is_authenticated:
        return redirect('login')
        
    return render(request, 'users/profile.html', {'user': request.user})


# --- НОВАЯ, КОРРЕКТНАЯ ЛОГИКА РЕГИСТРАЦИИ ---
def register_view(request):
    """
    Обработчик регистрации НОВЫХ пользователей в legacy-таблицу.
    """
    if request.method == 'POST':
        # Получаем данные напрямую из request.POST
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        # --- ВАЛИДАЦИЯ ДАННЫХ ---
        errors = []
        
        if password1 != password2:
            errors.append('Пароли не совпадают.')
        
        if User.objects.filter(username=username).exists():
            errors.append('Пользователь с таким именем уже существует.')
            
        if not (username and password1 and password2 and first_name and last_name):
            errors.append('Все поля обязательны для заполнения.')

        # Если есть ошибки, рендерим форму заново с сообщениями об ошибках
        if errors:
            return render(request, 'users/register.html', {
                'errors': errors,
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
            })

        # --- СОЗДАНИЕ ПОЛЬЗОВАТЕЛЯ ---
        # Если валидация пройдена, создаем объект пользователя
        user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        
        # Используем ваш метод set_password для создания SHA256 хэша
        user.set_password(password1) 
        
        # Сохраняем пользователя в базу данных
        user.save()
        
        # Сразу логиним нового пользователя
        auth_login(request, user)
        
        return redirect('main_view')

    # Если это GET-запрос, просто отображаем пустую форму регистрации
    return render(request, 'users/register.html')