from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="YDocState",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "media_uuid",
                    models.UUIDField(
                        db_index=True,
                        help_text="UUID of the MediaStore item this document belongs to.",
                        unique=True,
                        verbose_name="Media UUID",
                    ),
                ),
                (
                    "state_vector",
                    models.BinaryField(
                        help_text="Result of Y.encodeStateAsUpdate(doc) serialised as bytes.",
                        verbose_name="Y.js encoded state vector",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Y.js doc state",
                "verbose_name_plural": "Y.js doc states",
                "ordering": ["-updated_at"],
            },
        ),
    ]
