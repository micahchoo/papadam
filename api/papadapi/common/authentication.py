from __future__ import annotations

from typing import Any

from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class InternalServiceKeyAuthentication(BaseAuthentication):
    """Authenticate requests via the ``X-Internal-Key`` header.

    Returns ``(None, "internal-service")`` on success — no Django user is
    associated with this credential, but DRF's ``request.auth`` is set so
    downstream code can inspect it if needed.
    """

    def authenticate(self, request: Any) -> tuple[None, str] | None:  # type: ignore[override]  # TYPE_DEBT: DRF types are incomplete
        expected: str = getattr(settings, "INTERNAL_SERVICE_KEY", "")
        key: str = request.headers.get("X-Internal-Key", "")
        if not expected or key != expected:
            raise AuthenticationFailed("Invalid or missing internal service key.")
        return (None, "internal-service")
