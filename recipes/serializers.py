# recipes/serializers.py

from rest_framework import serializers
from .models import Recipe, User
import ast

class RecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = '__all__'


def to_representation(self, instance):
    representation = super().to_representation(instance)
    if isinstance(representation['ingredients'], str):
        representation['ingredients'] = ast.literal_eval(representation['ingredients'])
    if isinstance(representation['instructions'], str):
        representation['instructions'] = ast.literal_eval(representation['instructions'])
    return representation



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Hash the password before saving
        user = User.objects.create(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
   def validate(self, attrs):
    data = super().validate(attrs)
    data['username'] = self.user.username
    data['id'] = self.user.id
    data['email'] = self.user.email
    return data

