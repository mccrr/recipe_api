# recipes/serializers.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from .models import Recipe, User
import ast
from bson import ObjectId

class ObjectIdField(serializers.Field):
    def to_representation(self, value):
        return str(value)
    
    def to_internal_value(self, data):
        try:
            return ObjectId(data)
        except (TypeError, ValueError):
            raise serializers.ValidationError("Invalid ObjectId format")

class UserSerializer(serializers.ModelSerializer):
    id = ObjectIdField(required=False)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
    
class RecipeSerializer(serializers.ModelSerializer):
    id = ObjectIdField(required=False)
    
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

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['username'] = self.user.username
        data['id'] = str(self.user.id)  # Convert ObjectId to string
        data['email'] = self.user.email
        return data