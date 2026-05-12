from django.contrib import admin
from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'slug', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('category_name', 'slug', 'description')
    prepopulated_fields = {'slug': ('category_name',)}
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Category Information', {
            'fields': ('category_name', 'slug')
        }),
        ('Details', {
            'fields': ('description', 'status')
        }),
        ('System Information', {
            'fields': ('created_at',)
        }),
    )