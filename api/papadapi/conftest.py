"""
papadam — pytest fixtures and factory-boy factories.

All tests import from here via pytest's conftest auto-discovery.
Factories are in factories.py (same directory); this file wires them to fixtures.
"""

# ── Factories (inline — move to factories.py when they grow large) ────────────
import factory
import pytest
from factory.django import DjangoModelFactory
from rest_framework.test import APIClient

from papadapi.annotate.models import Annotation
from papadapi.archive.models import MediaStore
from papadapi.common.models import Group, Tags
from papadapi.users.models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")


class TagFactory(DjangoModelFactory):
    class Meta:
        model = Tags

    name = factory.Sequence(lambda n: f"tag_{n}")
    count = 1


class GroupFactory(DjangoModelFactory):
    class Meta:
        model = Group

    name = factory.Sequence(lambda n: f"group_{n}")
    description = factory.Faker("sentence")
    is_public = True
    is_active = True


class MediaStoreFactory(DjangoModelFactory):
    class Meta:
        model = MediaStore

    name = factory.Sequence(lambda n: f"media_{n}")
    description = factory.Faker("sentence")
    is_public = True
    group = factory.SubFactory(GroupFactory)
    orig_name = factory.LazyAttribute(lambda o: f"{o.name}.mp3")
    orig_size = 1024 * 1024
    file_extension = ".mp3"
    media_processing_status = "Yet to process"


class AnnotationFactory(DjangoModelFactory):
    class Meta:
        model = Annotation

    # The frontend sends the bare media UUID as media_reference_id (not a full URL).
    media_reference_id = "00000000-0000-0000-0000-000000000000"
    media_target = "t=0,10"
    annotation_text = factory.Faker("sentence")
    annotation_type = Annotation.AnnotationType.TEXT
    reply_to = None
    media_ref_uuid = None
    is_public = True
    group = factory.SubFactory(GroupFactory)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def admin_user(db):
    return UserFactory(is_staff=True, is_superuser=True)


@pytest.fixture
def group(db):
    return GroupFactory()


@pytest.fixture
def group_with_member(db, user):
    g = GroupFactory()
    g.users.add(user)
    return g


@pytest.fixture
def tag(db):
    return TagFactory()


@pytest.fixture
def media(db, group):
    return MediaStoreFactory(group=group)


@pytest.fixture
def annotation(db, media, group):
    return AnnotationFactory(
        media_reference_id=str(media.uuid),
        group=group,
    )


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, user):
    """Authenticated DRF test client (JWT)."""
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def member_media(db, group_with_member):
    """A MediaStore in the group that member_client belongs to."""
    return MediaStoreFactory(group=group_with_member)


@pytest.fixture
def member_annotation(db, member_media, group_with_member):
    """An Annotation whose media is in the member's group."""
    return AnnotationFactory(
        media_reference_id=str(member_media.uuid),
        group=group_with_member,
    )


@pytest.fixture
def member_client(api_client, group_with_member):
    """Client authenticated as a member of group_with_member."""
    user = group_with_member.users.first()
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    api_client.user = user
    api_client.group = group_with_member
    return api_client
