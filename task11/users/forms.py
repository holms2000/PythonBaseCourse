# users/forms.py

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

# Получаем текущую активную модель пользователя из настроек
User = get_user_model()

class RegisterForm(forms.ModelForm):
    """
    Форма для регистрации нового пользователя.
    """
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User # <-- ИСПРАВЛЕНО на User
        fields = ['username', 'password', 'first_name', 'last_name']
        # labels = {'username': 'Логин'}
        # help_texts = {'username': None} # Убираем стандартную подсказку

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
        Сохраняет пользователя с хешированием пароля.
        """
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    """
    Форма для входа в систему.
    """
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)