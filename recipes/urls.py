# recipes/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecipeViewSet, UserRegistrationView, LoginView

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipe')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
]