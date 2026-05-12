from django.db import migrations, models


def forwards(apps, schema_editor):
    Book = apps.get_model('book', 'Book')
    Category = apps.get_model('category', 'Category')
    db_alias = schema_editor.connection.alias

    for book in Book.objects.using(db_alias).exclude(category__isnull=True).exclude(category__exact='').iterator():
        category_slug = (book.category or 'book').strip() or 'book'
        category = Category.objects.using(db_alias).filter(slug=category_slug).first()
        if category is None:
            category, _ = Category.objects.using(db_alias).get_or_create(
                slug=category_slug,
                defaults={
                    'category_name': category_slug.replace('-', ' ').title() or 'Category',
                    'status': 'active',
                },
            )

        book.category_relation = category
        book.save(update_fields=['category_relation'])


def backwards(apps, schema_editor):
    Book = apps.get_model('book', 'Book')
    db_alias = schema_editor.connection.alias

    for book in Book.objects.using(db_alias).select_related('category_relation').exclude(category_relation__isnull=True).iterator():
        book.category = book.category_relation.slug
        book.save(update_fields=['category'])


class Migration(migrations.Migration):

    dependencies = [
        ('book', '0003_remove_category_choices'),
        ('category', '0002_alter_category_options_alter_category_created_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='category_relation',
            field=models.ForeignKey(null=True, on_delete=models.PROTECT, related_name='books', to='category.category'),
        ),
        migrations.RunPython(forwards, backwards),
        migrations.RemoveField(
            model_name='book',
            name='category',
        ),
        migrations.RenameField(
            model_name='book',
            old_name='category_relation',
            new_name='category',
        ),
        migrations.AlterField(
            model_name='book',
            name='category',
            field=models.ForeignKey(on_delete=models.PROTECT, related_name='books', to='category.category'),
        ),
    ]
