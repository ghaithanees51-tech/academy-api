from django import forms
from django.contrib import admin
from django.utils.html import format_html

from .gemini_service import extract_arabic_text_from_pdf
from .models import Book, BookChatLog, PublicationTextExtraction


class BookAdminForm(forms.ModelForm):
    extract_with_gemini = forms.BooleanField(
        required=False,
        label="Extract text with Gemini AI",
        help_text=(
            "Turn on to send the uploaded PDF to Gemini after saving. "
            "The extracted Arabic text and summary will be saved automatically. "
            "If extraction already exists it will be overwritten."
        ),
    )

    class Meta:
        model = Book
        fields = "__all__"


class TextExtractionInline(admin.StackedInline):
    model = PublicationTextExtraction
    extra = 0
    can_delete = True
    readonly_fields = ("arabic_text_preview", "summary", "created_at", "updated_at")
    fields = ("arabic_text_preview", "summary", "created_at", "updated_at")
    verbose_name = "Gemini Extraction Result"
    verbose_name_plural = "Gemini Extraction Result"

    def has_add_permission(self, request, obj=None):
        return False

    def arabic_text_preview(self, obj):
        if not obj.arabic_text:
            return "—"
        preview = obj.arabic_text[:800]
        if len(obj.arabic_text) > 800:
            preview += "…"
        return format_html(
            '<div style="direction:rtl;font-family:serif;line-height:1.8;white-space:pre-wrap">{}</div>',
            preview,
        )

    arabic_text_preview.short_description = "Arabic text (preview)"


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    form = BookAdminForm
    inlines = [TextExtractionInline]

    list_display = (
        "title",
        "type",
        "category",
        "author",
        "language",
        "status",
        "extraction_badge",
        "created_at",
    )

    list_filter = (
        "type",
        "category",
        "language",
        "status",
        "created_at",
    )

    search_fields = (
        "title",
        "author",
        "publisher",
        "isbn",
    )

    readonly_fields = ("created_at",)

    fieldsets = (
        (
            "Book Information",
            {
                "fields": (
                    "type",
                    "category",
                    "title",
                    "author",
                    "publisher",
                    "edition",
                    "year",
                    "isbn",
                    "language",
                    "pages",
                )
            },
        ),
        (
            "Media",
            {
                "fields": (
                    "cover",
                    "file",
                    "audio",
                    "video",
                    "audio_file",
                    "video_file",
                )
            },
        ),
        (
            "Details",
            {
                "fields": (
                    "date",
                    "status",
                )
            },
        ),
        (
            "Gemini AI Extraction",
            {
                "fields": ("extract_with_gemini",),
                "description": (
                    "Upload a PDF above, tick the toggle, then click Save — "
                    "Gemini will extract the Arabic text and summary automatically."
                ),
            },
        ),
        (
            "System Information",
            {"fields": ("created_at",)},
        ),
    )

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("text_extraction")

    def extraction_badge(self, obj):
        if hasattr(obj, "text_extraction"):
            return format_html(
                '<span style="color:#16a34a;font-weight:bold;">&#10003; Extracted</span>'
            )
        return format_html('<span style="color:#9ca3af;">— Not extracted</span>')

    extraction_badge.short_description = "Gemini"

    # ------------------------------------------------------------------ #
    # Save hook
    # ------------------------------------------------------------------ #

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if not form.cleaned_data.get("extract_with_gemini"):
            return

        if not obj.file:
            self.message_user(
                request,
                "Gemini extraction skipped: no PDF file attached to this book.",
                level="warning",
            )
            return

        try:
            result = extract_arabic_text_from_pdf(obj.file.path)
            PublicationTextExtraction.objects.update_or_create(
                book=obj,
                defaults={
                    "arabic_text": result["arabic_text"],
                    "summary": result["summary"],
                },
            )
            self.message_user(
                request,
                f'Gemini extraction completed for "{obj.title}".',
            )
        except Exception as exc:
            self.message_user(
                request,
                f"Gemini extraction failed: {exc}",
                level="error",
            )


@admin.register(BookChatLog)
class BookChatLogAdmin(admin.ModelAdmin):
    list_display = ("book", "short_question", "short_answer", "asked_at")
    list_filter = ("book", "asked_at")
    search_fields = ("question", "answer", "book__title")
    readonly_fields = ("book", "question", "answer", "asked_at")
    ordering = ("-asked_at",)

    def short_question(self, obj):
        return obj.question[:80] + ("…" if len(obj.question) > 80 else "")
    short_question.short_description = "Question"

    def short_answer(self, obj):
        return obj.answer[:80] + ("…" if len(obj.answer) > 80 else "")
    short_answer.short_description = "Answer"

    def has_add_permission(self, request):
        return False
