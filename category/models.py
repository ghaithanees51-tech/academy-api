from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )

    category_name = models.CharField(
        max_length=150,
        verbose_name='Category Name'
    )

    slug = models.SlugField(
        max_length=160,
        unique=True,
        blank=True,
        verbose_name='Slug'
    )

    description = models.TextField(
        blank=True,
        verbose_name='Description'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Status'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_category_name = self.category_name
        self._original_slug = self.slug

    def _build_unique_slug(self):
        base_slug = slugify(self.category_name, allow_unicode=False) or 'category'
        slug_candidate = base_slug
        suffix = 1

        while Category.objects.filter(slug=slug_candidate).exclude(pk=self.pk).exists():
            suffix += 1
            slug_candidate = f'{base_slug}-{suffix}'

        return slug_candidate

    def save(self, *args, **kwargs):
        original_category_name = getattr(self, '_original_category_name', self.category_name)
        original_slug = getattr(self, '_original_slug', self.slug)
        original_auto_slug = slugify(original_category_name, allow_unicode=False) or 'category'

        if not self.slug:
            self.slug = self._build_unique_slug()
        elif self.category_name != original_category_name and original_slug == original_auto_slug:
            self.slug = self._build_unique_slug()

        super().save(*args, **kwargs)
        self._original_category_name = self.category_name
        self._original_slug = self.slug

    def __str__(self):
        return self.category_name

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status']),
        ]