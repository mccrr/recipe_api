from mongoengine import DoesNotExist
from .models import User

class MongoEngineBackend:
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(username=username)
            if user.check_password(password) and user.is_active:
                return user
        except DoesNotExist:
            return None
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except DoesNotExist:
            return None