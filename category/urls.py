from django.urls import path
from .views import (
    CategoryDetailAPIView,
    CategoryListCreateAPIView,
    PublicCategoryListAPIView,
)

urlpatterns = [
    path('category/', CategoryListCreateAPIView.as_view(), name='category-list-create'),
    path('category/<int:pk>/', CategoryDetailAPIView.as_view(), name='category-detail'),
    path('categories/', CategoryListCreateAPIView.as_view(), name='category-list-create-legacy'),
    path('categories/<int:pk>/', CategoryDetailAPIView.as_view(), name='category-detail-legacy'),

    # Public – no auth required; used by the landing page to build the category tabs
    path('public/categories/', PublicCategoryListAPIView.as_view(), name='public-category-list'),
]
