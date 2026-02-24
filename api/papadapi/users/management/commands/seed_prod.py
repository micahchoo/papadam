"""
seed_prod — idempotent production data seed.

Creates (from environment variables):
  • Admin user — ADMIN_USERNAME (default "admin"), ADMIN_PASSWORD (required)
  • "Instance" group — admin as member
  • UIConfig on that group with defaults

Re-running is safe — uses get_or_create throughout.
The admin password is NOT reset if the user already exists (intentional).
"""

import os

import structlog
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from papadapi.common.models import Group, UIConfig

logger = structlog.get_logger(__name__)

User = get_user_model()


class Command(BaseCommand):
    help = "Seed production data (admin user, Instance group, UIConfig)"

    def handle(self, *args, **options):
        admin_username = os.environ.get("ADMIN_USERNAME", "admin")
        admin_password = os.environ.get("ADMIN_PASSWORD", "")

        if not admin_password:
            raise CommandError(
                "ADMIN_PASSWORD environment variable is required for seed_prod. "
                "Export it before running: export ADMIN_PASSWORD=<secret>"
            )

        # ── admin user ────────────────────────────────────────────────────────
        admin, created = User.objects.get_or_create(
            username=admin_username,
            defaults={
                "is_staff": True,
                "is_superuser": True,
                "first_name": "Admin",
                "last_name": "User",
            },
        )
        if created:
            admin.set_password(admin_password)
            admin.save()
            logger.info("created_user", username=admin_username, role="superuser")
            self.stdout.write(
                self.style.SUCCESS(f"  created admin user '{admin_username}'")
            )
        else:
            logger.info("existing_user", username=admin_username)
            self.stdout.write(
                self.style.WARNING(
                    f"  [WARN] admin user '{admin_username}' already exists — "
                    "password NOT changed."
                )
            )

        # ── Instance group ────────────────────────────────────────────────────
        group, created = Group.objects.get_or_create(
            name="Instance",
            defaults={"is_public": False, "is_active": True},
        )
        if created:
            logger.info("created_group", name="Instance")
            self.stdout.write("  created group 'Instance'")
        else:
            self.stdout.write("  skip group 'Instance' (already exists)")

        group.users.add(admin)

        # ── UIConfig ──────────────────────────────────────────────────────────
        _, created = UIConfig.objects.get_or_create(group=group)
        if created:
            logger.info("created_uiconfig", group="Instance")
            self.stdout.write("  created UIConfig for Instance group")
        else:
            self.stdout.write("  skip UIConfig (already exists)")

        self.stdout.write(self.style.SUCCESS("seed_prod complete."))
