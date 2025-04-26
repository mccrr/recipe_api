# recipes/serializers.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from mongoengine import Document
from .models import Recipe, User
from bson import ObjectId
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate

class ObjectIdField(serializers.Field):
    def to_representation(self, value):
        return str(value)
    
    def to_internal_value(self, data):
        try:
            return ObjectId(data)
        except (TypeError, ValueError):
            raise serializers.ValidationError("Invalid ObjectId format")

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['user_id'] = str(user.id)
        return token

    def validate(self, attrs):
        credentials = {
            'email': attrs.get('email'),
            'password': attrs.get('password')
        }
        user = authenticate(request=self.context.get('request'), **credentials)
        if not user:
            raise serializers.ValidationError('Invalid email or password.')

        data = {}
        refresh = self.get_token(user)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        data['username'] = user.username
        data['id'] = str(user.id)
        data['email'] = user.email
        return data

class UserSerializer(serializers.Serializer):
    id = ObjectIdField(read_only=True)
    username = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def create(self, validated_data):
        return User.manager.create_user(**validated_data)

    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        if 'password' in validated_data:
            instance.password = make_password(validated_data['password'])
        instance.save()
        return instance

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError('Must include both email and password.')

        user = authenticate(
            request=self.context.get('request'),
            email=email,
            password=password
        )
        if not user:
            raise serializers.ValidationError('Invalid email or password.')

        attrs['user'] = user
        return attrs

class RecipeSerializer(serializers.Serializer):
    id = ObjectIdField(read_only=True)
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(allow_blank=True)
    ingredients = serializers.ListField(child=serializers.CharField())
    instructions = serializers.ListField(child=serializers.CharField())
    image = serializers.CharField(allow_blank=True)

    def create(self, validated_data):
        return Recipe(**validated_data).save()

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    def to_representation(self, instance):
        representation = {
            'id': str(instance.id),
            'title': instance.title,
            'description': instance.description,
            'ingredients': instance.ingredients,
            'instructions': instance.instructions,
            'image': instance.image or ''
        }
        return representation