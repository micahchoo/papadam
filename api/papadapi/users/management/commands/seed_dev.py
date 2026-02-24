"""
seed_dev — idempotent development data seed.

Creates:
  • admin / admin    — superuser  (INSECURE — change in production)
  • demo  / demo     — regular user
  • "Demo Community" group — demo user as member
  • UIConfig on that group with default branding
  • Tags: interview, music, documentary, oral-history, archive, field-recording

All objects are created with get_or_create — safe to re-run.
"""

import structlog
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from papadapi.common.models import Group, Tags, UIConfig

logger = structlog.get_logger(__name__)

User = get_user_model()

_SEED_TAGS = [
    "interview",
    "music",
    "documentary",
    "oral-history",
    "archive",
    "field-recording",
]


class Command(BaseCommand):
    help = "Seed development data (admin/admin, demo/demo, Demo Community group, tags)"

    def handle(self, *args, **options):
        # ── admin superuser ───────────────────────────────────────────────────
        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "is_staff": True,
                "is_superuser": True,
                "first_name": "Admin",
                "last_name": "User",
            },
        )
        if created:
            admin.set_password("admin")
            admin.save()
            logger.info("created_user", username="admin", role="superuser")
            self.stdout.write(
                self.style.WARNING(
                    "  [INSECURE] Created admin/admin "
                    "— change this password in production!"
                )
            )
        else:
            logger.info("existing_user", username="admin")
            self.stdout.write("  skip admin (already exists)")

        # ── demo user ─────────────────────────────────────────────────────────
        demo, created = User.objects.get_or_create(
            username="demo",
            defaults={"first_name": "Demo", "last_name": "User"},
        )
        if created:
            demo.set_password("demo")
            demo.save()
            logger.info("created_user", username="demo", role="member")
            self.stdout.write("  created demo/demo")
        else:
            logger.info("existing_user", username="demo")
            self.stdout.write("  skip demo (already exists)")

        # ── Demo Community group ──────────────────────────────────────────────
        group, created = Group.objects.get_or_create(
            name="Demo Community",
            defaults={"is_public": True, "is_active": True},
        )
        if created:
            logger.info("created_group", name="Demo Community")
            self.stdout.write("  created group 'Demo Community'")
        else:
            self.stdout.write("  skip group 'Demo Community' (already exists)")

        group.users.add(demo)

        # ── UIConfig ──────────────────────────────────────────────────────────
        config, created = UIConfig.objects.get_or_create(group=group)
        if created:
            logger.info("created_uiconfig", group="Demo Community")
            self.stdout.write("  created UIConfig for Demo Community")
        else:
            self.stdout.write("  skip UIConfig (already exists)")

        # ── Tags ──────────────────────────────────────────────────────────────
        for tag_name in _SEED_TAGS:
            _, created = Tags.objects.get_or_create(name=tag_name)
            if created:
                logger.info("created_tag", name=tag_name)
                self.stdout.write(f"  created tag '{tag_name}'")
            else:
                self.stdout.write(f"  skip tag '{tag_name}' (already exists)")

        self.stdout.write(self.style.SUCCESS("seed_dev complete."))
