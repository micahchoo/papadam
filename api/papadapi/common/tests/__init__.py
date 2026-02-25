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


# ── UIConfig signal ────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestUIConfigSignal:
    def test_creating_group_auto_creates_uiconfig(self) -> None:
        from papadapi.common.models import Group, UIConfig

        group = Group.objects.create(name="Signal Test Group")
        assert UIConfig.objects.filter(group=group).exists()

    def test_uiconfig_has_correct_defaults(self) -> None:
        from papadapi.common.models import Group, UIConfig

        group = Group.objects.create(name="Defaults Group")
        cfg = UIConfig.objects.get(group=group)
        assert cfg.brand_name == "Papad.alt"
        assert cfg.primary_color == "#1e3a5f"
        assert cfg.accent_color == "#3b82f6"
        assert cfg.profile == "standard"
        assert cfg.color_scheme == "default"

    def test_uiconfig_not_duplicated_on_second_save(self) -> None:
        from papadapi.common.models import Group, UIConfig

        group = Group.objects.create(name="No Dup Group")
        group.name = "Updated"
        group.save()
        assert UIConfig.objects.filter(group=group).count() == 1


# ── UIConfig view ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestUIConfigView:
    def test_get_anon_returns_200(self, api_client) -> None:
        resp = api_client.get("/api/v1/uiconfig/")
        assert resp.status_code == 200
        assert resp.data["brand_name"] == "Papad.alt"

    def test_get_anon_has_required_fields(self, api_client) -> None:
        resp = api_client.get("/api/v1/uiconfig/")
        assert resp.status_code == 200
        for field in ("profile", "primary_color", "accent_color", "color_scheme"):
            assert field in resp.data

    def test_get_anon_has_nested_sub_objects(self, api_client) -> None:
        resp = api_client.get("/api/v1/uiconfig/")
        assert resp.status_code == 200
        pc = resp.data["player_controls"]
        assert "skip_seconds" in pc
        assert len(pc["skip_seconds"]) == 2
        assert "show_waveform" in pc
        assert "show_transcript" in pc
        assert "default_quality" in pc
        ac = resp.data["annotations_config"]
        assert "allow_images" in ac
        assert "allow_audio" in ac
        assert "allow_video" in ac
        assert "allow_media_ref" in ac
        assert "time_range_input" in ac
        ec = resp.data["exhibit_config"]
        assert "enabled" in ec

    def test_get_auth_with_group_returns_config(self, member_client) -> None:
        resp = member_client.get("/api/v1/uiconfig/")
        assert resp.status_code == 200
        assert "profile" in resp.data
        assert "brand_name" in resp.data

    def test_patch_updates_brand_name(self, member_client) -> None:
        from papadapi.common.models import UIConfig

        resp = member_client.patch(
            "/api/v1/uiconfig/",
            data={"brand_name": "My Community"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["brand_name"] == "My Community"
        cfg = UIConfig.objects.get(group=member_client.group)
        assert cfg.brand_name == "My Community"

    def test_patch_requires_auth(self, api_client) -> None:
        resp = api_client.patch(
            "/api/v1/uiconfig/",
            data={"brand_name": "Anon"},
            format="json",
        )
        assert resp.status_code == 401

    def test_patch_player_controls_round_trips(self, member_client) -> None:
        from papadapi.common.models import UIConfig

        payload = {
            "player_controls": {
                "skip_seconds": [5, 15],
                "show_waveform": True,
                "show_transcript": True,
                "default_quality": "low",
            }
        }
        resp = member_client.patch("/api/v1/uiconfig/", data=payload, format="json")
        assert resp.status_code == 200
        pc = resp.data["player_controls"]
        assert pc["skip_seconds"] == [5, 15]
        assert pc["show_waveform"] is True
        assert pc["default_quality"] == "low"
        cfg = UIConfig.objects.get(group=member_client.group)
        assert cfg.player_controls["skip_seconds"] == [5, 15]

    def test_patch_annotations_config_round_trips(self, member_client) -> None:
        from papadapi.common.models import UIConfig

        payload = {
            "annotations_config": {
                "allow_images": False,
                "allow_audio": True,
                "allow_video": False,
                "allow_media_ref": True,
                "time_range_input": "timestamp",
            }
        }
        resp = member_client.patch("/api/v1/uiconfig/", data=payload, format="json")
        assert resp.status_code == 200
        ac = resp.data["annotations_config"]
        assert ac["allow_images"] is False
        assert ac["time_range_input"] == "timestamp"
        cfg = UIConfig.objects.get(group=member_client.group)
        assert cfg.annotations_config["allow_images"] is False

    def test_patch_exhibit_config_round_trips(self, member_client) -> None:
        from papadapi.common.models import UIConfig

        resp = member_client.patch(
            "/api/v1/uiconfig/",
            data={"exhibit_config": {"enabled": False}},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["exhibit_config"]["enabled"] is False
        cfg = UIConfig.objects.get(group=member_client.group)
        assert cfg.exhibit_config["enabled"] is False


# ── Endpoint tests: HealthCheck, RuntimeConfig, Groups, Tags ──────────────────


@pytest.mark.django_db
class TestHealthCheckEndpoint:
    def test_healthcheck_returns_200(self, api_client) -> None:
        resp = api_client.get("/healthcheck/")
        assert resp.status_code == 200


@pytest.mark.django_db
class TestRuntimeConfigEndpoint:
    def test_config_json_returns_200_anon(self, api_client) -> None:
        resp = api_client.get("/config.json")
        assert resp.status_code == 200
        assert "API_URL" in resp.data
        assert "CRDT_URL" in resp.data


@pytest.mark.django_db
class TestGroupEndpoints:
    def test_list_groups_returns_200_anon(self, api_client) -> None:
        resp = api_client.get("/api/v1/group/")
        assert resp.status_code == 200

    def test_list_groups_contains_public_group(self, api_client, group) -> None:
        resp = api_client.get("/api/v1/group/")
        assert resp.status_code == 200
        names = [g["name"] for g in resp.data["results"]]
        assert group.name in names

    def test_retrieve_group_by_id(self, api_client, group) -> None:
        resp = api_client.get(f"/api/v1/group/{group.id}/")
        assert resp.status_code == 200
        assert resp.data["name"] == group.name

    def test_retrieve_nonexistent_group_returns_404(self, api_client) -> None:
        resp = api_client.get("/api/v1/group/999999/")
        assert resp.status_code == 404

    def test_create_group_requires_auth(self, api_client) -> None:
        resp = api_client.post(
            "/api/v1/group/", data={"name": "test"}, format="json"
        )
        assert resp.status_code == 401


@pytest.mark.django_db
class TestTagsEndpoints:
    def test_list_tags_returns_200(self, api_client) -> None:
        resp = api_client.get("/api/v1/tags/")
        assert resp.status_code == 200

    def test_create_tag_requires_auth(self, api_client) -> None:
        resp = api_client.post(
            "/api/v1/tags/", data={"name": "newtag"}, format="json"
        )
        assert resp.status_code == 401


# ── Adversarial endpoint tests ───────────────────────────────────────────────


@pytest.mark.django_db
class TestCommonAdversarial:
    def test_group_retrieve_negative_id_returns_404(self, api_client) -> None:
        resp = api_client.get("/api/v1/group/-1/")
        assert resp.status_code == 404

    def test_uiconfig_patch_authed_user_no_group_returns_404(
        self, auth_client,
    ) -> None:
        resp = auth_client.patch(
            "/api/v1/uiconfig/",
            data={"brand_name": "No Group"},
            format="json",
        )
        assert resp.status_code == 404

    def test_uiconfig_patch_invalid_font_scale_returns_400(
        self, member_client,
    ) -> None:
        resp = member_client.patch(
            "/api/v1/uiconfig/",
            data={"font_scale": "not_a_number"},
            format="json",
        )
        assert resp.status_code == 400
