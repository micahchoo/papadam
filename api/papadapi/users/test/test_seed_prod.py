import os
from unittest.mock import patch

import pytest
from django.core.management import call_command

from papadapi.common.models import Group, UIConfig


@pytest.mark.django_db
def test_seed_prod_creates_group_from_env():
    """seed_prod uses SEED_ env vars for group name, language, and branding."""
    env = {
        "ADMIN_PASSWORD": "testpass123",
        "SEED_GROUP_NAME": "TestVillage",
        "SEED_GROUP_LANGUAGE": "kn",
        "SEED_BRAND_NAME": "Village Archive",
        "SEED_BRAND_PRIMARY": "#2d5a27",
        "SEED_BRAND_ACCENT": "#e6a817",
    }
    with patch.dict(os.environ, env):
        call_command("seed_prod")

    group = Group.objects.get(name="TestVillage")
    uiconfig = UIConfig.objects.get(group=group)
    assert uiconfig.language == "kn"
    assert uiconfig.brand_name == "Village Archive"
    assert uiconfig.primary_color == "#2d5a27"
    assert uiconfig.accent_color == "#e6a817"


@pytest.mark.django_db
def test_seed_prod_defaults_without_seed_vars():
    """seed_prod uses sensible defaults when no SEED_ vars are set."""
    env = {"ADMIN_PASSWORD": "testpass123"}
    with patch.dict(os.environ, env):
        call_command("seed_prod")

    group = Group.objects.get(name="Community")
    uiconfig = UIConfig.objects.get(group=group)
    assert uiconfig.language == "en"
    assert uiconfig.brand_name == "Community"


@pytest.mark.django_db
def test_seed_prod_idempotent():
    """Running seed_prod twice does not duplicate."""
    env = {"ADMIN_PASSWORD": "testpass123"}
    with patch.dict(os.environ, env):
        call_command("seed_prod")
        call_command("seed_prod")
    assert Group.objects.filter(name="Community").count() == 1


@pytest.mark.django_db
def test_seed_prod_requires_admin_password():
    """seed_prod raises CommandError when ADMIN_PASSWORD is missing."""
    from django.core.management.base import CommandError

    with pytest.raises(CommandError, match="ADMIN_PASSWORD"):
        call_command("seed_prod")
