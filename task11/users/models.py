import hashlib
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import _user_has_perm

class LegacyUserManager(BaseUserManager):
    def get_by_natural_key(self, username):
        return self.get(username=username)

    # Остальные методы можно оставить как есть или реализовать при необходимости
    def create_user(self, username, password=None):
        raise NotImplementedError("Создание через ORM не поддерживается.")

class LegacyUser(AbstractBaseUser):
    username = models.CharField(max_length=150, unique=True, primary_key=True)
    
    # ВАЖНО: Поле 'password' здесь НЕ объявляем,
    # так как оно есть в AbstractBaseUser и мы его переопределим.
    
    password_hash = models.CharField(max_length=255)
    first_name = models.CharField(max_length=100, db_column='firstname')
    last_name = models.CharField(max_length=100, db_column='lastname')
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []
    
    objects = LegacyUserManager()

    class Meta:
        managed = False 
        db_table = 'users'

    # --- РЕШЕНИЕ ПРОБЛЕМЫ С ОШИБКОЙ SQL ---
    # Этот блок кода говорит Django: "Не ищи поля password, last_login,
    # is_active, is_staff, is_superuser в базе данных. Они являются свойствами".
    def _get_password(self):
        return self.password_hash

    def _set_password(self, value):
        self.password_hash = value

    # Создаем property-объекты для полей, которых нет в БД
    password = property(_get_password, _set_password)
    last_login = None # Или можно сделать property, если логика нужна

    # Свойства для прав доступа
    @property
    def is_superuser(self):
        return self.username == 'admin' # Ваша логика

    @property
    def is_staff(self):
        return self.is_superuser

    @property
    def is_active(self):
        return True

    # --- Методы аутентификации ---
    def check_password(self, raw_password):
        return self.password_hash == hashlib.sha256(raw_password.encode()).hexdigest()

    def set_password(self, raw_password):
        self.password_hash = hashlib.sha256(raw_password.encode()).hexdigest()

    # --- Метод проверки прав ---
    def has_perm(self, perm, obj=None):
        if self.is_superuser:
            return True
        return _user_has_perm(self, perm, obj)

    def has_module_perms(self, app_label):
        return self.is_superuser

    # Методы для совместимости
    def get_group_permissions(self, obj=None):
        return set()

    def get_all_permissions(self, obj=None):
        return set()
    
    @property
    def user_permissions(self):
        return []