from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Fix mutable default on MediaStore.extra_group_response.
    default=[] → default=list (callable).  DB schema is unchanged (still nullable jsonb).
    """

    dependencies = [
        ('archive', '0021_rename_is_media_processing_mediastore_media_processing_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mediastore',
            name='extra_group_response',
            field=models.JSONField(blank=True, default=list, null=True),
        ),
    ]
