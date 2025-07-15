from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # For students, use roll_number
            if 'roll_number' in kwargs:
                user = User.objects.get(roll_number=kwargs['roll_number'])
            else:
                # For teachers, use username
                user = User.objects.get(username=username)
            
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
