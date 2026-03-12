"""
seed_prod — idempotent production data seed.

Creates (from environment variables):
  • Admin user — ADMIN_USERNAME (default "admin"), ADMIN_PASSWORD (required)
  • Group — SEED_GROUP_NAME (default "Community"), admin as member
  • UIConfig — SEED_GROUP_LANGUAGE, SEED_BRAND_NAME, SEED_BRAND_PRIMARY,
    SEED_BRAND_ACCENT (all with sensible defaults)

Re-running is safe — uses get_or_create / update_or_create throughout.
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
    help = "Seed production data (admin user, group, UIConfig from SEED_ env vars)"

    def handle(self, *args: object, **options: object) -> None:
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
        group_name = os.environ.get("SEED_GROUP_NAME", "Community")
        group, created = Group.objects.get_or_create(
            name=group_name,
            defaults={"is_public": False, "is_active": True},
        )
        if created:
            logger.info("created_group", name=group_name)
            self.stdout.write(f"  created group '{group_name}'")
        else:
            self.stdout.write(f"  skip group '{group_name}' (already exists)")

        group.users.add(admin)

        # ── UIConfig ──────────────────────────────────────────────────────────
        # Group post_save signal auto-creates UIConfig with model defaults.
        # Use update_or_create to apply SEED_ overrides regardless.
        _, created = UIConfig.objects.update_or_create(
            group=group,
            defaults={
                "language": os.environ.get("SEED_GROUP_LANGUAGE", "en"),
                "brand_name": os.environ.get("SEED_BRAND_NAME", group_name),
                "primary_color": os.environ.get("SEED_BRAND_PRIMARY", "#1e3a5f"),
                "accent_color": os.environ.get("SEED_BRAND_ACCENT", "#d97706"),
            },
        )
        if created:
            logger.info("created_uiconfig", group=group_name)
            self.stdout.write(f"  created UIConfig for {group_name} group")
        else:
            logger.info("updated_uiconfig", group=group_name)
            self.stdout.write(f"  updated UIConfig for {group_name} group")

        self.stdout.write(self.style.SUCCESS("seed_prod complete."))
