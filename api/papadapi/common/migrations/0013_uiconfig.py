import django.db.models.deletion
from django.db import migrations, models

import papadapi.common.models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0012_alter_group_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='UIConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('profile', models.CharField(
                    choices=[
                        ('standard', 'Standard'),
                        ('icon', 'Icon'),
                        ('voice', 'Voice'),
                        ('high-contrast', 'High Contrast'),
                    ],
                    default='standard',
                    max_length=20,
                )),
                ('brand_name', models.CharField(default='Papad.alt', max_length=100)),
                ('brand_logo_url', models.CharField(blank=True, default='', max_length=500)),
                ('primary_color', models.CharField(default='#1e3a5f', max_length=7)),
                ('accent_color', models.CharField(default='#3b82f6', max_length=7)),
                ('language', models.CharField(default='en', max_length=10)),
                ('icon_set', models.CharField(default='default', max_length=200)),
                ('font_scale', models.FloatField(default=1.0)),
                ('color_scheme', models.CharField(
                    choices=[
                        ('default', 'Default'),
                        ('warm', 'Warm'),
                        ('cool', 'Cool'),
                        ('high-contrast', 'High Contrast'),
                    ],
                    default='default',
                    max_length=20,
                )),
                ('voice_enabled', models.BooleanField(default=False)),
                ('offline_first', models.BooleanField(default=False)),
                ('player_controls', models.JSONField(default=papadapi.common.models._default_player_controls)),
                ('annotations_config', models.JSONField(default=papadapi.common.models._default_annotations_config)),
                ('exhibit_config', models.JSONField(default=papadapi.common.models._default_exhibit_config)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('group', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='uiconfig',
                    to='common.group',
                )),
            ],
            options={
                'verbose_name': 'UI Configuration',
            },
        ),
    ]
