# users/forms.py

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class RegisterForm(forms.ModelForm):
    """
    Форма для регистрации нового пользователя.
    """
    # Поле для подтверждения пароля не является частью модели, поэтому мы добавляем его здесь
    confirm_password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        # Используем fields, чтобы указать, какие поля из модели нам нужны
        fields = ['username', 'first_name', 'last_name'] 
        # Обратите внимание: 'password' здесь нет, потому что мы используем password_hash

    def clean(self):
        """
        Проверяет, что пароли совпадают.
        """
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise ValidationError("Пароли не совпадают.")
            
    def save(self, commit=True):
        """
        Сохраняет пользователя с хешированием пароля через НАШ метод set_password.
        """
        user = super().save(commit=False)
        
        # Получаем пароль из cleaned_data и передаем его в наш кастомный метод
        user.set_password(self.cleaned_data["password"])
        
        if commit:
            user.save()
        return user

# --- ДОБАВЬТЕ ЭТОТ КЛАСС В КОНЕЦ ФАЙЛА ---
class LoginForm(forms.Form):
    """
    Форма для входа в систему.
    Не является ModelForm, так как не сохраняет данные в базу.
    """
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)