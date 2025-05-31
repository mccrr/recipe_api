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
import logging

logger = logging.getLogger(__name__)

class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'recent_recipes', 'recipes_by_ingredients']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return Recipe.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    def get_object(self):
        pk = self.kwargs.get('pk')
        try:
            ObjectId(pk)
            recipe = Recipe.objects.get(id=pk)
            return recipe
        except (DoesNotExist, InvalidId):
            raise NotFound(detail="Recipe not found.")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        recipe = self.get_object()
        try:
            Likes.objects.filter(recipe=recipe).delete()
            Bookmarks.objects.filter(recipe=recipe).delete()
            recipe.delete()
            logger.info(f"Deleted recipe {recipe.id} with associated likes and bookmarks")
            return Response(status=204)
        except Exception as e:
            logger.error(f"Error deleting recipe {recipe.id}: {str(e)}")
            return Response({"detail": "Failed to delete recipe and associated data."}, status=500)

    @action(detail=False, methods=['get'], url_path='recent')
    def recent_recipes(self, request):
        limit = int(request.query_params.get('limit', 5))
        if limit not in [5, 10]:
            limit = 5
        recipes = Recipe.objects.order_by('-createdAt')[:limit]
        serializer = self.get_serializer(recipes, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='by-ingredients')
    def recipes_by_ingredients(self, request):
        ingredients = request.data.get('ingredients', [])
        if not ingredients or not isinstance(ingredients, list):
            return Response({"detail": "Ingredients list is required."}, status=400)
        ingredients = [ingredient.lower().strip() for ingredient in ingredients]
        recipes = Recipe.objects.all()
        matching_recipes = []
        for recipe in recipes:
            required_ingredients = [ing.lower().strip() for ing in recipe.ingredients]
            if not required_ingredients:
                continue
            matched_ingredients = [ing for ing in required_ingredients if ing in ingredients]
            match_percentage = (len(matched_ingredients) / len(required_ingredients)) * 100
            if match_percentage >= 50:
                recipe_data = RecipeSerializer(recipe, context={'request': request}).data
                recipe_data['ingredient_match_percentage'] = round(match_percentage, 2)
                matching_recipes.append(recipe_data)
        matching_recipes.sort(key=lambda x: x['ingredient_match_percentage'], reverse=True)
        return Response(matching_recipes)

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
    serializer_class = BookmarksSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Bookmarks.objects.none()
        return Bookmarks.objects(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    def get_object(self):
        pk = self.kwargs.get('pk')
        try:
            ObjectId(pk)
            bookmark = Bookmarks.objects.get(id=pk)
            if bookmark.user != self.request.user:
                raise PermissionDenied(detail="You do not have permission to access this bookmark.")
            return bookmark
        except (DoesNotExist, InvalidId):
            raise NotFound(detail="Bookmark not found.")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='toggle')
    def toggle_bookmark(self, request):
        recipe_id = request.data.get('recipe')
        if not recipe_id:
            return Response({"detail": "Recipe ID is required."}, status=400)
        
        try:
            ObjectId(recipe_id)
            recipe = Recipe.objects.get(id=recipe_id)
        except (DoesNotExist, InvalidId):
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
        bookmark_ids = [b.recipe.id for b in Bookmarks.objects(user=request.user)]
        bookmarked_recipes = Recipe.objects(id__in=bookmark_ids)
        serializer = RecipeSerializer(bookmarked_recipes, many=True, context={'request': request})
        return Response(serializer.data)

class LikesViewSet(viewsets.ModelViewSet):
    serializer_class = LikesSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Likes.objects.none()
        return Likes.objects(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    def get_object(self):
        pk = self.kwargs.get('pk')
        try:
            ObjectId(pk)
            like = Likes.objects.get(id=pk)
            if like.user != self.request.user:
                raise PermissionDenied(detail="You do not have permission to access this like.")
            return like
        except (DoesNotExist, InvalidId):
            raise NotFound(detail="Like not found.")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='toggle')
    def toggle_like(self, request):
        recipe_id = request.data.get('recipe')
        if not recipe_id:
            return Response({"detail": "Recipe ID is required."}, status=400)
        
        try:
            ObjectId(recipe_id)
            recipe = Recipe.objects.get(id=recipe_id)
        except (DoesNotExist, InvalidId):
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
        like_ids = [l.recipe.id for l in Likes.objects(user=request.user)]
        liked_recipes = Recipe.objects(id__in=like_ids)
        serializer = RecipeSerializer(liked_recipes, many=True, context={'request': request})
        return Response(serializer.data)