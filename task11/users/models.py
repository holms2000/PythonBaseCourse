# users/models.py

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

class LegacyUser(AbstractBaseUser, PermissionsMixin):
    """
    Модель-посредник для работы с существующей таблицей пользователей 'users'.
    Не создает и не изменяет таблицу в базе данных (managed = False).
    """
    # Основные поля аутентификации
    username = models.CharField(max_length=150, unique=True)
    password_hash = models.CharField(max_length=255) # Поле из вашей старой базы

    # Поля профиля пользователя
    # Параметр db_column указывает Django на реальные имена столбцов в вашей БД
    first_name = models.CharField(max_length=100, db_column='firstname')
    last_name = models.CharField(max_length=100, db_column='lastname')
    
    # Поле email (если оно есть в вашей базе, добавьте его аналогично)
    # email = models.EmailField(db_column='email', blank=True, null=True)

    # Обязательные поля для кастомной модели пользователя
    USERNAME_FIELD = 'username'
    
    class Meta:
        # Указываем, что таблица уже существует и ее не нужно трогать
        managed = False 
        # Точное имя таблицы из вашей базы данных
        db_table = 'users'

    def __str__(self):
        """Строковое представление объекта."""
        return self.username

    def check_password(self, raw_password):
        """
        Проверяет пароль.
        Сравнивает хеш от переданного пароля с хешем, хранящимся в password_hash.
        """
        from hashlib import sha256
        return self.password_hash == sha256(raw_password.encode()).hexdigest()

    # Следующие методы могут потребоваться Django для полноценной работы.
    # Если вы столкнетесь с ошибками в админке, раскомментируйте их.
    
    # @property
    # def is_staff(self):
    #     """Все ли пользователи являются персоналом (для доступа к админке)?"""
    #     # По умолчанию, только суперпользователи имеют доступ к админке.
    #     return self.is_superuser

    # @property
    # def is_active(self):
    #     """Активен ли пользователь?"""
    #     return True