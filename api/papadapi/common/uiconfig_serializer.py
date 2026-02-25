from __future__ import annotations

from rest_framework import serializers

from .models import UIConfig


class UIConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = UIConfig
        fields = (
            "profile",
            "brand_name",
            "brand_logo_url",
            "primary_color",
            "accent_color",
            "language",
            "icon_set",
            "font_scale",
            "color_scheme",
            "voice_enabled",
            "offline_first",
            "player_controls",
            "annotations_config",
            "exhibit_config",
            "updated_at",
        )
        read_only_fields = ("updated_at",)
