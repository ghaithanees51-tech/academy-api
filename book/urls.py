from django.urls import path
from .views import (
    BookListCreateAPIView,
    BookDetailAPIView,
    PublicationExtractArabicTextView,
    PublicationExtractionView,
)

urlpatterns = [
    path('books/', BookListCreateAPIView.as_view(), name='book-list-create'),
    path('books/<int:pk>/', BookDetailAPIView.as_view(), name='book-detail'),

    path('publications/', BookListCreateAPIView.as_view(), name='publication-list-create'),
    path('publications/<int:pk>/', BookDetailAPIView.as_view(), name='publication-detail'),

    # Gemini auto-extract (force=true to overwrite)
    path('publications/<int:pk>/extract-arabic-text/', PublicationExtractArabicTextView.as_view(), name='publication-extract-arabic-text'),

    # Manual save / fetch extraction
    path('publications/<int:pk>/extraction/', PublicationExtractionView.as_view(), name='publication-extraction'),
]
