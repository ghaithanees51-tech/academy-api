from django.db import models

from category.models import Category


class Book(models.Model):
    TYPE_CHOICES = (
        ('pdf', 'PDF'),
        ('audio', 'Audio'),
        ('video', 'Video'),
    )

    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='pdf')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='books')

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    publisher = models.CharField(max_length=255, blank=True)
    edition = models.CharField(max_length=100, blank=True)
    year = models.CharField(max_length=10, blank=True)
    isbn = models.CharField(max_length=50, blank=True)

    language = models.CharField(max_length=100, default='العربية')
    pages = models.PositiveIntegerField(null=True, blank=True)

    audio = models.URLField(blank=True)
    video = models.URLField(blank=True)
    audio_file = models.FileField(upload_to='publications/audio/', null=True, blank=True)
    video_file = models.FileField(upload_to='publications/video/', null=True, blank=True)

    cover = models.ImageField(upload_to='publications/covers/', null=True, blank=True)
    file = models.FileField(upload_to='publications/documents/', null=True, blank=True)

    date = models.CharField(max_length=20, blank=True)

    status = models.CharField(
        max_length=20,
        choices=(('active', 'Active'), ('inactive', 'Inactive')),
        default='active'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Book'
        verbose_name_plural = 'Books'
        ordering = ['-id']

    def __str__(self):
        return self.title

class PublicationTextExtraction(models.Model):
    book = models.OneToOneField(
        Book,
        on_delete=models.CASCADE,
        related_name="text_extraction"
    )
    arabic_text = models.TextField()
    summary = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Text extraction for {self.book}"

class BookChatLog(models.Model):
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="chat_logs",
    )
    question = models.TextField()
    answer = models.TextField()
    asked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Chat Log"
        verbose_name_plural = "Chat Logs"
        ordering = ["-asked_at"]

    def __str__(self):
        return f"[{self.book.title}] {self.question[:60]}"


class BookSummary(models.Model):
    class Meta:
        verbose_name = 'Book Summary'
        verbose_name_plural = 'Book Summaries'
        ordering = ['-id']

    book = models.OneToOneField(Book, on_delete=models.CASCADE, related_name="summary")
    summary = models.TextField()
    key_points = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Summary - {self.book.title}"