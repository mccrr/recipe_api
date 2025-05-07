from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound, PermissionDenied
from .models import Recipe, User, Bookmarks, Likes
from .serializers import RecipeSerializer, UserSerializer, LoginSerializer, CustomTokenObtainPairSerializer, BookmarksSerializer, LikesSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from mongoengine.errors import DoesNotExist
from bson import ObjectId
from bson.errors import InvalidId

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self):
        """
        Override get_object to handle MongoEngine querysets and raise 404 for non-existent recipes.
        """
        pk = self.kwargs.get('pk')
        try:
            ObjectId(pk)
            recipe = Recipe.objects.get(id=pk)
            return recipe
        except (DoesNotExist, InvalidId, ValueError):
            raise NotFound(detail="Recipe not found.")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

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

    def get_queryset(self):
        """
        Return bookmarks only for the authenticated user.
        """
        if not self.request.user.is_authenticated:
            return Bookmarks.objects.none()
        return Bookmarks.objects(user=self.request.user)

    def list(self, request, *args, **kwargs):
        """
        Override list to ensure only the authenticated user's bookmarks are returned.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_object(self):
        """
        Override get_object to handle MongoEngine querysets and ensure only the bookmark's owner can access/delete it.
        """
        pk = self.kwargs.get('pk')
        try:
            ObjectId(pk)
            bookmark = Bookmarks.objects.get(id=pk)
            if bookmark.user != self.request.user:
                raise PermissionDenied(detail="You do not have permission to access this bookmark.")
            return bookmark
        except (DoesNotExist, InvalidId, ValueError):
            raise NotFound(detail="Bookmark not found.")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='toggle')
    def toggle_bookmark(self, request):
        """
        Toggle bookmark for a recipe. If bookmarked, delete it; otherwise, create it.
        """
        recipe_id = request.data.get('recipe')
        if not recipe_id:
            return Response({"detail": "Recipe ID is required."}, status=400)
        
        try:
            ObjectId(recipe_id)
            recipe = Recipe.objects.get(id=recipe_id)
        except (DoesNotExist, InvalidId, ValueError):
            return Response({"detail": "Recipe not found."}, status=404)

        bookmark = Bookmarks.objects(user=request.user, recipe=recipe).first()
        if bookmark:
            bookmark.delete()
            return Response({"detail": "Bookmark removed.", "is_bookmarked": False}, status=200)
        else:
            bookmark = Bookmarks(user=request.user, recipe=recipe)
            bookmark.save()
            return Response({"detail": "Bookmark added.", "is_bookmarked": True}, status=201)

    @action(detail=False, methods=['get'], url_path='recipes')
    def list_bookmarked_recipes(self, request):
        bookmarked_recipes = Recipe.objects.filter(id__in=Bookmarks.objects(user=request.user).values_list('recipe'))
        serializer = RecipeSerializer(bookmarked_recipes, many=True, context={'request': request})
        return Response(serializer.data)

class LikesViewSet(viewsets.ModelViewSet):
    queryset = Likes.objects.all()
    serializer_class = LikesSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        Override get_object to handle MongoEngine querysets and ensure only the like's owner can access/delete it.
        """
        pk = self.kwargs.get('pk')
        try:
            ObjectId(pk)
            like = Likes.objects.get(id=pk)
            if like.user != self.request.user:
                raise PermissionDenied(detail="You do not have permission to access this like.")
            return like
        except (DoesNotExist, InvalidId, ValueError):
            raise NotFound(detail="Like not found.")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return Likes.objects(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='toggle')
    def toggle_like(self, request):
        """
        Toggle like for a recipe. If liked, delete it; otherwise, create it.
        """
        recipe_id = request.data.get('recipe')
        if not recipe_id:
            return Response({"detail": "Recipe ID is required."}, status=400)
        
        try:
            ObjectId(recipe_id)
            recipe = Recipe.objects.get(id=recipe_id)
        except (DoesNotExist, InvalidId, ValueError):
            return Response({"detail": "Recipe not found."}, status=404)

        like = Likes.objects(user=request.user, recipe=recipe).first()
        if like:
            like.delete()
            return Response({"detail": "Like removed.", "is_liked": False}, status=200)
        else:
            like = Likes(user=request.user, recipe=recipe)
            like.save()
            return Response({"detail": "Like added.", "is_liked": True}, status=201)

    @action(detail=False, methods=['get'], url_path='recipes')
    def list_liked_recipes(self, request):
        liked_recipes = Recipe.objects.filter(id__in=Likes.objects(user=request.user).values_list('recipe'))
        serializer = RecipeSerializer(liked_recipes, many=True, context={'request': request})
        return Response(serializer.data)