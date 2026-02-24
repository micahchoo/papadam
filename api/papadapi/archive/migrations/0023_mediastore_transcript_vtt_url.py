from django.db import migrations, models


class Migration(migrations.Migration):
    """Add transcript_vtt_url to MediaStore for Whisper VTT captions."""

    dependencies = [
        ('archive', '0022_fix_extra_group_response_default'),
    ]

    operations = [
        migrations.AddField(
            model_name='mediastore',
            name='transcript_vtt_url',
            field=models.URLField(
                blank=True,
                default='',
                max_length=500,
                verbose_name='Transcript VTT URL',
            ),
        ),
    ]
