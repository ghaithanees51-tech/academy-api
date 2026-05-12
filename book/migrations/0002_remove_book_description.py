from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("book", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="book",
            name="description",
        ),
    ]
