"""
Tests for papadapi.common.functions.

create_or_update_tag  — tag normalisation + get-or-create + count refresh
get_final_tags_count  — pure data merge, no DB required
"""

import pytest

from papadapi.common.functions import create_or_update_tag, get_final_tags_count
from papadapi.common.models import Tags


# ── create_or_update_tag ──────────────────────────────────────────────────────


@pytest.mark.django_db
class TestCreateOrUpdateTag:
    def test_creates_new_tag(self) -> None:
        tag = create_or_update_tag("Nature")
        assert tag is not None
        assert Tags.objects.filter(name="nature").exists()

    def test_lowercases_and_strips(self) -> None:
        tag = create_or_update_tag("  River  ")
        assert tag is not None
        assert tag.name == "river"

    def test_returns_existing_tag(self) -> None:
        t1 = create_or_update_tag("forest")
        t2 = create_or_update_tag("forest")
        assert t1 is not None
        assert t2 is not None
        assert t1.pk == t2.pk
        assert Tags.objects.filter(name="forest").count() == 1

    def test_empty_string_returns_none(self) -> None:
        result = create_or_update_tag("")
        assert result is None

    def test_whitespace_only_returns_none(self) -> None:
        result = create_or_update_tag("   ")
        assert result is None

    def test_new_tag_count_initialised_to_one(self) -> None:
        tag = create_or_update_tag("unique-tag-xyz")
        assert tag is not None
        tag.refresh_from_db()
        # No MediaStore or Annotation references → recalculate sets count=1
        assert tag.count == 1


# ── get_final_tags_count ──────────────────────────────────────────────────────


class TestGetFinalTagsCount:
    """Pure data-transformation function — no DB access required."""

    def test_count_mode_merges_counts(self) -> None:
        media = [{"tag_id": 1, "count": 3}]
        anno = [{"tag_id": 1, "count": 2}]
        result = get_final_tags_count(media, anno, count=True)
        assert len(result) == 1
        assert result[0]["count"] == 5

    def test_count_mode_distinct_keys(self) -> None:
        media = [{"tag_id": 1, "count": 1}]
        anno = [{"tag_id": 2, "count": 4}]
        result = get_final_tags_count(media, anno, count=True)
        assert len(result) == 2

    def test_count_mode_empty_inputs(self) -> None:
        result = get_final_tags_count([], [], count=True)
        assert result == []

    def test_non_count_mode_merges_symbol_size(self) -> None:
        media = [{"id": 10, "symbolSize": 5, "tag_in": True, "category": 0}]
        anno = [{"id": 10, "symbolSize": 6, "tag_in": False, "category": 1}]
        result = get_final_tags_count(media, anno, count=False)
        assert len(result) == 1
        assert result[0]["symbolSize"] >= 8  # min clamp

    def test_non_count_mode_distinct_ids(self) -> None:
        media = [{"id": 1, "symbolSize": 5, "tag_in": True, "category": 0}]
        anno = [{"id": 2, "symbolSize": 3, "tag_in": False, "category": 1}]
        result = get_final_tags_count(media, anno, count=False)
        assert len(result) == 2
