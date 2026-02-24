from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Fix mutable default on Group.group_extra_questions.
    default={} → default=dict (callable).  DB schema is unchanged (still nullable jsonb).
    """

    dependencies = [
        ('common', '0013_uiconfig'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='group_extra_questions',
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
    ]
