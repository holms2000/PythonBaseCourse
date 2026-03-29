# users/authentication.py

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

class LegacyUserBackend(BaseBackend):
    """
    Кастомный бэкенд для аутентификации через модель LegacyUser.
    """
    def authenticate(self, *args, **kwargs):
        # Этот метод не будет использоваться в нашей логике входа,
        # но он должен быть. Оставляем его пустым или возвращаем None.
        return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None