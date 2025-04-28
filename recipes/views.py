from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Recipe, User, Bookmarks
from .serializers import RecipeSerializer, UserSerializer, LoginSerializer, CustomTokenObtainPairSerializer, BookmarksSerializer
from rest_framework.parsers import MultiPartParser, FormParser

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

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
            'username': user.username,
            'password': request.data['password']
        })
        token_serializer.is_valid(raise_exception=True)
        return Response(token_serializer.validated_data)

class BookmarksViewSet(viewsets.ModelViewSet):
    queryset = Bookmarks.objects.all()
    serializer_class = BookmarksSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return Bookmarks.objects(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='recipes')
    def list_bookmarked_recipes(self, request):
        bookmarked_recipes = Recipe.objects.filter(id__in=Bookmarks.objects(user=request.user).values_list('recipe'))
        serializer = RecipeSerializer(bookmarked_recipes, many=True, context={'request': request})
        return Response(serializer.data)