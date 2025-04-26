# recipes/models.py
from mongoengine import Document, StringField, EmailField, BooleanField, ListField
from django.contrib.auth.hashers import make_password, check_password

class UserManager:
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        user = User(username=username, email=email, **extra_fields)
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
    image = StringField()

    meta = {
        'collection': 'recipes'
    }

    def __str__(self):
        return self.title