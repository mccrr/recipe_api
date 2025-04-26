# recipes/jwt_auth.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from .models import User
from mongoengine import DoesNotExist

class MongoEngineJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        try:
            user_id = validated_token['user_id']
            user = User.objects.get(id=user_id)
            if not user.is_active:
                raise InvalidToken('User account is disabled.')
            return user
        except (KeyError, DoesNotExist):
            raise InvalidToken('User not found.')