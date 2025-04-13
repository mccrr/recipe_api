# recipes/views.py
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework import viewsets
from .models import Recipe
from .serializers import RecipeSerializer

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer

# views.py
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import User
from .serializers import UserSerializer
from django.contrib.auth import authenticate

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    if request.method == 'POST':
        # Initialize the serializer with request data
        serializer = UserSerializer(data=request.data)
        
        if serializer.is_valid():
            # Save the new user
            user = serializer.save()
            
            # Serialize the user object to return the response
            user_data = UserSerializer(user).data
            
            # Return a success message and serialized user data
            return Response({"message": "User created successfully", "user": user_data}, status=status.HTTP_201_CREATED)
        
        # If validation fails, return the validation errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .serializers import CustomTokenObtainPairSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    # Authenticate user
    user = authenticate(username=username, password=password)
    
    if user:
        # If user is authenticated, create the refresh and access tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Return the tokens in the response along with user information
        return Response({
            'access': access_token,
            'refresh': str(refresh),
            'username': user.username,
            'id': user.id,
            'email': user.email
        }, status=status.HTTP_200_OK)
    
    # If authentication fails, return an error response
    return Response({"message": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
