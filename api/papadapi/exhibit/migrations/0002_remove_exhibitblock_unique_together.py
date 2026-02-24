"""Remove (exhibit, order) unique_together from ExhibitBlock.

Bulk reorder requires updating multiple rows without triggering
the constraint mid-transaction. Ordering is enforced at the
application level via ExhibitBlockSerializer.validate() and the
reorder_blocks view action.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("exhibit", "0001_initial"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="exhibitblock",
            unique_together=set(),
        ),
    ]
