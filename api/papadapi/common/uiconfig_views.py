from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Group, UIConfig
from .uiconfig_serializer import UIConfigSerializer

# Hardcoded default payload — avoids serializing an unsaved model instance
# and allows anonymous access without touching the DB.
_DEFAULT: dict = {
    "profile": "standard",
    "brand_name": "Papad.alt",
    "brand_logo_url": "",
    "primary_color": "#1e3a5f",
    "accent_color": "#3b82f6",
    "language": "en",
    "icon_set": "default",
    "font_scale": 1.0,
    "color_scheme": "default",
    "voice_enabled": False,
    "offline_first": False,
    "player_controls": {
        "skip_seconds": [10, 30],
        "show_waveform": False,
        "show_transcript": False,
        "default_quality": "auto",
    },
    "annotations_config": {
        "allow_images": True,
        "allow_audio": True,
        "allow_video": True,
        "allow_media_ref": True,
        "time_range_input": "slider",
    },
    "exhibit_config": {"enabled": True},
    "updated_at": None,
}


class UIConfigView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        if request.user.is_anonymous:
            return Response(_DEFAULT)
        group = (
            Group.objects.filter(users=request.user)
            .select_related("uiconfig")
            .first()
        )
        if group is None:
            return Response(_DEFAULT)
        config, _ = UIConfig.objects.get_or_create(group=group)
        return Response(UIConfigSerializer(config).data)

    def patch(self, request: Request) -> Response:
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication required."}, status=401)
        group = (
            Group.objects.filter(users=request.user)
            .select_related("uiconfig")
            .first()
        )
        if group is None:
            return Response({"detail": "No group found for this user."}, status=404)
        config, _ = UIConfig.objects.get_or_create(group=group)
        serializer = UIConfigSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
