from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category
from .serializers import CategorySerializer


class BaseCategoryAPIView:
    permission_classes = [IsAuthenticated]
    pagination_class = None


class CategoryListCreateAPIView(BaseCategoryAPIView, ListCreateAPIView):
    queryset = Category.objects.all().order_by('-id')
    serializer_class = CategorySerializer


class CategoryDetailAPIView(BaseCategoryAPIView, RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all().order_by('-id')
    serializer_class = CategorySerializer


class PublicCategoryListAPIView(APIView):
    """Public endpoint: returns active categories as {id, label} pairs for the landing page."""
    permission_classes = [AllowAny]
    http_method_names = ['get', 'head', 'options']

    def get(self, request):
        categories = Category.objects.filter(status='active').order_by('id')
        data = [{'id': cat.slug, 'label': cat.category_name} for cat in categories]
        return Response(data)

