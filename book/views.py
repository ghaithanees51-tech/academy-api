import logging

from django.db.models import Count, Exists, OuterRef, Subquery

logger = logging.getLogger(__name__)
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Book, BookChatLog, PublicationTextExtraction
from .gemini_service import answer_question_from_arabic_text, extract_arabic_text_from_pdf
from .serializers import BookSerializer, PublicPublicationSerializer


def _is_arabic_language(value: str | None) -> bool:
    normalized = (value or "").strip().lower()
    return "العربية" in normalized or "arabic" in normalized


def _public_book_qs():
    """Books annotated with extraction status directly from the DB — no reverse-accessor magic."""
    return (
        Book.objects
        .select_related('category')
        .annotate(
            _has_text_extraction=Exists(
                PublicationTextExtraction.objects.filter(book_id=OuterRef('pk'))
            ),
            _extraction_summary=Subquery(
                PublicationTextExtraction.objects
                .filter(book_id=OuterRef('pk'))
                .values('summary')[:1]
            ),
        )
        .filter(status='active')
        .order_by('-id')
    )

class BaseBookAPIView:
    permission_classes = [IsAuthenticated]
    pagination_class = None

class BookListCreateAPIView(BaseBookAPIView, ListCreateAPIView):
    queryset = Book.objects.select_related('category', 'text_extraction').all().order_by('-id')
    serializer_class = BookSerializer

class BookDetailAPIView(BaseBookAPIView, RetrieveUpdateDestroyAPIView):
    queryset = Book.objects.select_related('category', 'text_extraction').all().order_by('-id')
    serializer_class = BookSerializer

    # File fields that can be cleared via remove_<field>=true in PATCH body
    _CLEARABLE_FILE_FIELDS = ('cover', 'file', 'audio_file', 'video_file')

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        for field in self._CLEARABLE_FILE_FIELDS:
            remove_key = f'remove_{field}'
            if request.data.get(remove_key) == 'true':
                file_field = getattr(instance, field)
                if file_field:
                    file_field.delete(save=False)
                setattr(instance, field, None)

        instance.save(update_fields=self._CLEARABLE_FILE_FIELDS)
        return super().update(request, *args, **kwargs)

class PublicPublicationListAPIView(ListCreateAPIView):
    permission_classes = [AllowAny]
    pagination_class = None
    serializer_class = PublicPublicationSerializer
    http_method_names = ['get', 'head', 'options']

    def get_queryset(self):
        qs = _public_book_qs()
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category__slug=category)
        return qs

class PublicPublicationDetailAPIView(RetrieveAPIView):
    permission_classes = [AllowAny]
    pagination_class = None
    serializer_class = PublicPublicationSerializer
    http_method_names = ['get', 'head', 'options']

    def get_queryset(self):
        return _public_book_qs()

class PublicPublicationStatsAPIView(APIView):
    permission_classes = [AllowAny]
    http_method_names = ['get', 'head', 'options']

    def get(self, request):
        counts = {
            row['category__slug']: row['count']
            for row in Book.objects.filter(status='active')
            .values('category__slug')
            .annotate(count=Count('id'))
        }
        return Response({
            'total': sum(counts.values()),
            'counts': counts,
        })


class PublicPublicationSummaryAPIView(APIView):
    permission_classes = [AllowAny]
    http_method_names = ['get', 'head', 'options']

    def get(self, request, pk):
        # Resolve by book_id directly, as requested by frontend page route.
        if not Book.objects.filter(pk=pk).exists():
            return Response(
                {"message": "Book not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        extraction = PublicationTextExtraction.objects.filter(book_id=pk).first()
        return Response({
            "book_id": pk,
            "has_text_extraction": extraction is not None,
            "summary": extraction.summary if extraction else None,
        })

class PublicationExtractionView(APIView):
    """GET: fetch saved extraction. POST: save manually-entered text."""
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'options']

    def _get_book(self, pk):
        try:
            return Book.objects.get(pk=pk), None
        except Book.DoesNotExist:
            return None, Response(
                {"message": "Book not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    def get(self, request, pk):
        book, err = self._get_book(pk)
        if err:
            return err
        existing = PublicationTextExtraction.objects.filter(book=book).first()
        if not existing:
            return Response(
                {"message": "No extraction found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({
            "book_id": book.id,
            "arabic_text": existing.arabic_text,
            "summary": existing.summary,
            "created_at": existing.created_at,
            "updated_at": existing.updated_at,
        })

    def post(self, request, pk):
        book, err = self._get_book(pk)
        if err:
            return err
        arabic_text = (request.data.get("arabic_text") or "").strip()
        summary = (request.data.get("summary") or "").strip()
        if not arabic_text:
            return Response(
                {"message": "arabic_text is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        extraction, created = PublicationTextExtraction.objects.update_or_create(
            book=book,
            defaults={"arabic_text": arabic_text, "summary": summary},
        )
        return Response({
            "message": "Extraction saved" if not created else "Extraction created",
            "book_id": book.id,
            "arabic_text": extraction.arabic_text,
            "summary": extraction.summary,
        }, status=status.HTTP_200_OK)


class PublicationExtractArabicTextView(APIView):
    """Send PDF to Gemini and save the result. Pass force=true to overwrite existing."""
    permission_classes = [AllowAny]
    http_method_names = ['post', 'options']

    def post(self, request, pk):
        try:
            book = Book.objects.get(pk=pk)
        except Book.DoesNotExist:
            return Response(
                {"message": "Book not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if not _is_arabic_language(book.language):
            return Response(
                {"message": "Only Arabic PDFs can be extracted"},
                status=status.HTTP_400_BAD_REQUEST
            )

        force = str(request.data.get("force", "false")).lower() == "true"

        existing = PublicationTextExtraction.objects.filter(book=book).first()

        if existing and not force:
            return Response({
                "message": "Already extracted",
                "from_cache": True,
                "book_id": book.id,
                "arabic_text": existing.arabic_text,
                "summary": existing.summary,
            })

        if not book.file:
            return Response(
                {"message": "PDF file not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = extract_arabic_text_from_pdf(book.file.path)

            extraction, _ = PublicationTextExtraction.objects.update_or_create(
                book=book,
                defaults={
                    "arabic_text": result["arabic_text"],
                    "summary": result["summary"],
                },
            )

            return Response({
                "message": "Arabic text extracted successfully",
                "from_cache": False,
                "book_id": book.id,
                "arabic_text": extraction.arabic_text,
                "summary": extraction.summary,
            })

        except Exception as error:
            return Response(
                {
                    "message": "Gemini processing failed",
                    "error": str(error),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PublicationAskAPIView(APIView):
    permission_classes = [AllowAny]
    http_method_names = ['post', 'options']

    def post(self, request, pk):
        try:
            book = Book.objects.get(pk=pk)
        except Book.DoesNotExist:
            return Response(
                {"message": "Book not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        question = (request.data.get("question") or "").strip()
        if not question:
            return Response(
                {"message": "question is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        extraction = PublicationTextExtraction.objects.filter(book=book).first()
        if not extraction or not extraction.arabic_text.strip():
            return Response(
                {"message": "No Arabic text extraction found for this book"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            answer = answer_question_from_arabic_text(
                arabic_text=extraction.arabic_text,
                question=question,
                title=book.title,
            )
            answer = answer or "لم يتمكن Gemini من إنشاء إجابة."

            BookChatLog.objects.create(
                book=book,
                question=question,
                answer=answer,
            )

            return Response({
                "book_id": book.id,
                "answer": answer,
            })
        except Exception as error:
            logger.exception("Gemini ask failed for book %s: %s", pk, error)
            return Response(
                {
                    "message": "Gemini processing failed",
                    "error": str(error),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PublicationChatHistoryAPIView(APIView):
    permission_classes = [AllowAny]
    http_method_names = ['get', 'options']

    def get(self, request, pk):
        if not Book.objects.filter(pk=pk).exists():
            return Response(
                {"message": "Book not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        logs = (
            BookChatLog.objects
            .filter(book_id=pk)
            .order_by('asked_at')
            .values('id', 'question', 'answer', 'asked_at')
        )
        return Response(list(logs))