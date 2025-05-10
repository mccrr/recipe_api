from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from mongoengine import Document
from .models import Recipe, User, Bookmarks, Likes
from bson import ObjectId
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate
import base64
import json
import logging

# Set up logging
logger = logging.getLogger(__name__)

class ObjectIdField(serializers.Field):
    def to_representation(self, value):
        return str(value)
    
    def to_internal_value(self, data):
        try:
            return ObjectId(data)
        except (TypeError, ValueError):
            raise serializers.ValidationError("Invalid ObjectId format")

class JSONListField(serializers.Field):
    def to_internal_value(self, data):
        if isinstance(data, str):
            try:
                data = data.replace('\\"', '"')
                parsed_data = json.loads(data)
            except json.JSONDecodeError:
                raise serializers.ValidationError("Must be a valid JSON array of strings")
        else:
            parsed_data = data
        if not isinstance(parsed_data, list) or not all(isinstance(item, str) for item in parsed_data):
            raise serializers.ValidationError("Must be a list of strings")
        return parsed_data

    def to_representation(self, value):
        return value

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['user_id'] = str(user.id)
        return token

    def validate(self, attrs):
        credentials = {
            'username': attrs.get('username'),
            'password': attrs.get('password')
        }
        user = authenticate(request=self.context.get('request'), **credentials)
        if not user:
            raise serializers.ValidationError('Invalid username or password.')

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
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if not username or not password:
            raise serializers.ValidationError('Must include both username and password.')

        user = authenticate(
            request=self.context.get('request'),
            username=username,
            password=password
        )
        if not user:
            raise serializers.ValidationError('Invalid username or password.')

        attrs['user'] = user
        return attrs

class BookmarksSerializer(serializers.Serializer):
    id = ObjectIdField(read_only=True)
    user = ObjectIdField(read_only=True)
    recipe = ObjectIdField()

    def validate(self, attrs):
        """
        Check if a bookmark already exists for the user and recipe.
        """
        user = self.context['request'].user
        recipe = attrs.get('recipe')
        if Bookmarks.objects(user=user, recipe=recipe).count() > 0:
            raise serializers.ValidationError("Bookmark already exists for this user and recipe.")
        return attrs

    def validate_recipe(self, value):
        """
        Ensure the recipe exists before creating a bookmark.
        """
        try:
            Recipe.objects.get(id=value)
        except (Recipe.DoesNotExist, ValueError):
            raise serializers.ValidationError("Recipe does not exist.")
        return value

    def create(self, validated_data):
        return Bookmarks(**validated_data).save()

    def to_representation(self, instance):
        try:
            representation = {
                'id': str(instance.id),
                'user': str(instance.user.id),
                'recipe': str(instance.recipe.id) if instance.recipe else None
            }
        except Recipe.DoesNotExist:
            representation = {
                'id': str(instance.id),
                'user': str(instance.user.id),
                'recipe': None
            }
        return representation

class LikesSerializer(serializers.Serializer):
    id = ObjectIdField(read_only=True)
    user = ObjectIdField(read_only=True)
    recipe = ObjectIdField()

    def validate(self, attrs):
        """
        Check if a like already exists for the user and recipe.
        """
        user = self.context['request'].user
        recipe = attrs.get('recipe')
        if Likes.objects(user=user, recipe=recipe).count() > 0:
            raise serializers.ValidationError("Like already exists for this user and recipe.")
        return attrs

    def validate_recipe(self, value):
        """
        Ensure the recipe exists before creating a like.
        """
        try:
            Recipe.objects.get(id=value)
        except (Recipe.DoesNotExist, ValueError):
            raise serializers.ValidationError("Recipe does not exist.")
        return value

    def create(self, validated_data):
        return Likes(**validated_data).save()

    def to_representation(self, instance):
        try:
            representation = {
                'id': str(instance.id),
                'user': str(instance.user.id),
                'recipe': str(instance.recipe.id) if instance.recipe else None
            }
        except Recipe.DoesNotExist:
            representation = {
                'id': str(instance.id),
                'user': str(instance.user.id),
                'recipe': None
            }
        return representation

class RecipeSerializer(serializers.Serializer):
    id = ObjectIdField(read_only=True)
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(allow_blank=True)
    ingredients = JSONListField()
    instructions = JSONListField()
    image = serializers.ImageField(required=False, allow_null=True)
    user = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    prep_time = serializers.IntegerField(min_value=0, required=False, allow_null=True)
    food_type = serializers.ChoiceField(choices=['Breakfast', 'Lunch', 'Dinner', 'Dessert', 'Snack'], required=False, allow_null=True)
    servings = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    likes_count = serializers.SerializerMethodField()
    bookmarks_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    def get_user(self, obj):
        return {
            'id': str(obj.user.id),
            'username': obj.user.username
        }

    def get_is_bookmarked(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return Bookmarks.objects(user=request.user, recipe=obj).count() > 0
        return False

    def get_likes_count(self, obj):
        return Likes.objects(recipe=obj).count()

    def get_bookmarks_count(self, obj):
        return Bookmarks.objects(recipe=obj).count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return Likes.objects(user=request.user, recipe=obj).count() > 0
        return False

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
            'prep_time': instance.prep_time,
            'food_type': instance.food_type,
            'servings': instance.servings,
            'likes_count': self.get_likes_count(instance),
            'bookmarks_count': self.get_bookmarks_count(instance),
            'is_liked': self.get_is_liked(instance),
            'user': self.get_user(instance),
            'is_bookmarked': self.get_is_bookmarked(instance)
        }
        if instance.image:
            try:
                gridfs_id = instance.image.grid_id
                if gridfs_id:
                    image_data = instance.image.read()
                    if image_data:
                        representation['image'] = base64.b64encode(image_data).decode('utf-8')
                    else:
                        logger.warning(f"Empty image data for recipe {instance.id}, GridFS ID: {gridfs_id}")
                        representation['image'] = None
                else:
                    logger.warning(f"No GridFS ID for image in recipe {instance.id}")
                    representation['image'] = None
            except Exception as e:
                logger.error(f"Failed to read image for recipe {instance.id}: {str(e)}")
                representation['image'] = None
        else:
            representation['image'] = None
        return representation