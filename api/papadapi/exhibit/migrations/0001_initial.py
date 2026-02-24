import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("common", "0012_alter_group_description"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Exhibit",
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
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("title", models.CharField(max_length=255, verbose_name="Title")),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="Description"),
                ),
                (
                    "is_public",
                    models.BooleanField(default=True, verbose_name="Public"),
                ),
                (
                    "group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="exhibits",
                        to="common.group",
                        verbose_name="Group",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="exhibits",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Created by",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Exhibit",
                "verbose_name_plural": "Exhibits",
                "ordering": ["-updated_at"],
            },
        ),
        migrations.CreateModel(
            name="ExhibitBlock",
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
                    "block_type",
                    models.CharField(
                        choices=[("media", "Media item"), ("annotation", "Annotation")],
                        default="media",
                        max_length=20,
                        verbose_name="Block type",
                    ),
                ),
                (
                    "media_uuid",
                    models.UUIDField(
                        blank=True,
                        help_text="UUID of the MediaStore item for media-type blocks.",
                        null=True,
                        verbose_name="Media UUID",
                    ),
                ),
                (
                    "annotation_uuid",
                    models.UUIDField(
                        blank=True,
                        help_text="UUID of the Annotation for annotation-type blocks.",
                        null=True,
                        verbose_name="Annotation UUID",
                    ),
                ),
                ("caption", models.TextField(blank=True, verbose_name="Caption")),
                (
                    "order",
                    models.PositiveIntegerField(
                        db_index=True, default=0, verbose_name="Display order"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "exhibit",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="blocks",
                        to="exhibit.exhibit",
                        verbose_name="Exhibit",
                    ),
                ),
            ],
            options={
                "verbose_name": "Exhibit block",
                "verbose_name_plural": "Exhibit blocks",
                "ordering": ["exhibit", "order"],
                "unique_together": {("exhibit", "order")},
            },
        ),
    ]
