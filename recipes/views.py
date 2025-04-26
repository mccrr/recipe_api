# recipes/views.py
from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.response import Response
from .models import Recipe, User
from .serializers import RecipeSerializer, UserSerializer, LoginSerializer, CustomTokenObtainPairSerializer

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token_serializer = CustomTokenObtainPairSerializer(data={
            'email': user.email,
            'password': request.data['password']  # Password already validated
        })
        token_serializer.is_valid(raise_exception=True)
        return Response(token_serializer.validated_data)