"""Tests that import_annotation enforces the same validation as the API."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from papadapi.annotate.models import Annotation
from papadapi.importexport.tasks import import_annotation

if TYPE_CHECKING:
    from papadapi.archive.models import MediaStore


@pytest.mark.django_db
def test_import_rejects_invalid_annotation_type(
    member_media: MediaStore, tmp_path: str,
) -> None:
    """import_annotation must not create annotations with invalid types."""
    initial_count = Annotation.objects.count()
    result = import_annotation(
        str(tmp_path),
        {
            "annotation_text": "test",
            "media_target": "t=0,5",
            "annotation_type": "BOGUS",
        },
        member_media,
    )
    assert result is False
    assert Annotation.objects.count() == initial_count
