"""
Tests for CrdtServerTokenAuthentication.

Verifies that the static shared-secret authenticator correctly accepts the
configured server token and falls through for everything else, leaving
JWTAuthentication to handle regular user sessions.
"""

from django.test import override_settings
from rest_framework.test import APIRequestFactory

from papadapi.crdt.views import CrdtServerTokenAuthentication, _CrdtServerUser

factory = APIRequestFactory()


class TestCrdtServerTokenAuthentication:
    def test_valid_token_authenticates(self) -> None:
        req = factory.get("/", HTTP_AUTHORIZATION="Bearer test-secret-abc")
        auth = CrdtServerTokenAuthentication()
        with override_settings(CRDT_SERVER_TOKEN="test-secret-abc"):
            result = auth.authenticate(req)
        assert result is not None
        user, token = result
        assert isinstance(user, _CrdtServerUser)
        assert user.is_authenticated is True
        assert user.is_crdt_server is True
        assert token is None

    def test_wrong_token_returns_none(self) -> None:
        req = factory.get("/", HTTP_AUTHORIZATION="Bearer wrong-token")
        auth = CrdtServerTokenAuthentication()
        with override_settings(CRDT_SERVER_TOKEN="correct-token"):
            result = auth.authenticate(req)
        assert result is None

    def test_empty_server_token_setting_returns_none(self) -> None:
        req = factory.get("/", HTTP_AUTHORIZATION="Bearer any-token")
        auth = CrdtServerTokenAuthentication()
        with override_settings(CRDT_SERVER_TOKEN=""):
            result = auth.authenticate(req)
        assert result is None

    def test_missing_authorization_header_returns_none(self) -> None:
        req = factory.get("/")
        auth = CrdtServerTokenAuthentication()
        with override_settings(CRDT_SERVER_TOKEN="my-secret"):
            result = auth.authenticate(req)
        assert result is None

    def test_non_bearer_scheme_returns_none(self) -> None:
        req = factory.get("/", HTTP_AUTHORIZATION="Basic dXNlcjpwYXNz")
        auth = CrdtServerTokenAuthentication()
        with override_settings(CRDT_SERVER_TOKEN="dXNlcjpwYXNz"):
            result = auth.authenticate(req)
        assert result is None
