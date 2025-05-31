from mongoengine import Document, StringField, EmailField, BooleanField, ListField, ReferenceField, DateTimeField, ImageField, IntField
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone

class UserManager:
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        if not username:
            raise ValueError("Users must have a username")
        user = User(
            username=username,
            email=email,
            createdAt=timezone.now(),
            **extra_fields
        )
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)

class User(Document):
    username = StringField(max_length=255, unique=True, required=True)
    email = EmailField(unique=True, required=True)
    password = StringField(required=True)
    is_staff = BooleanField(default=False)
    is_superuser = BooleanField(default=False)
    is_active = BooleanField(default=True)
    createdAt = DateTimeField(default=timezone.now)

    meta = {
        'collection': 'users'
    }

    manager = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

class Recipe(Document):
    title = StringField(max_length=255, required=True)
    description = StringField()
    ingredients = ListField(StringField())
    instructions = ListField(StringField())
    image = ImageField()
    user = ReferenceField(User, required=True)
    prep_time = IntField(min_value=0)
    food_type = StringField(choices=['Yemek', 'Tatlı', 'İçecek', 'Çorba'])
    servings = IntField(min_value=1)
    createdAt = DateTimeField(default=timezone.now)

    meta = {
        'collection': 'recipes'
    }

    def to_dict(self):
        recipe_dict = {
            'id': str(self.id),
            'title': self.title,
            'description': self.description,
            'ingredients': self.ingredients,
            'instructions': self.instructions,
            'image': str(self.image) if self.image else None,
            'prep_time': self.prep_time,
            'food_type': self.food_type,
            'servings': self.servings,
            'user': {
                'id': str(self.user.id),
                'username': self.user.username if self.user else 'Unknown'
            },
            'createdAt': self.createdAt.isoformat() if self.createdAt else None
        }
        return recipe_dict

class Bookmarks(Document):
    user = ReferenceField(User, required=True)
    recipe = ReferenceField(Recipe, required=True)

    meta = {
        'collection': 'bookmarks',
        'indexes': [
            {'fields': ['user', 'recipe'], 'unique': True}
        ]
    }

    def __str__(self):
        return f"{self.user.username} bookmarked {self.recipe.title}"

class Likes(Document):
    user = ReferenceField(User, required=True)
    recipe = ReferenceField(Recipe, required=True)

    meta = {
        'collection': 'likes',
        'indexes': [
            {'fields': ['user', 'recipe'], 'unique': True}
        ]
    }

    def __str__(self):
        return f"{self.user.username} liked {self.recipe.title}"