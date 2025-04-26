# recipe_api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from recipes.views import RecipeViewSet

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipe')

urlpatterns = [
    path('api/', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('users/', include('recipes.urls')),
]