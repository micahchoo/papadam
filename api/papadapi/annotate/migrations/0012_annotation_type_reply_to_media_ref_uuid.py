import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("annotate", "0011_annotation_group"),
    ]

    operations = [
        migrations.AddField(
            model_name="annotation",
            name="annotation_type",
            field=models.CharField(
                choices=[
                    ("text", "Text"),
                    ("image", "Image"),
                    ("audio", "Audio"),
                    ("video", "Video"),
                    ("media_ref", "Media Reference"),
                ],
                default="text",
                max_length=20,
                verbose_name="Annotation type",
            ),
        ),
        migrations.AddField(
            model_name="annotation",
            name="reply_to",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="replies",
                to="annotate.annotation",
                verbose_name="Reply to annotation",
            ),
        ),
        migrations.AddField(
            model_name="annotation",
            name="media_ref_uuid",
            field=models.UUIDField(
                blank=True,
                null=True,
                verbose_name="Referenced media UUID",
            ),
        ),
    ]
