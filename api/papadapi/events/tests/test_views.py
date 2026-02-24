"""Tests for the events/jobs status endpoint."""

from unittest.mock import patch

import pytest


@pytest.mark.django_db
def test_job_status_requires_auth(api_client):
    resp = api_client.get("/api/v1/events/jobs/some-job-id/")
    assert resp.status_code == 401


@pytest.mark.django_db
def test_job_status_not_found_when_arq_unavailable(auth_client):
    """When ARQ isn't wired (ARQ_AVAILABLE=False), return 503."""
    with patch("papadapi.events.views.ARQ_AVAILABLE", False):
        resp = auth_client.get("/api/v1/events/jobs/fake-job-id/")
    assert resp.status_code == 503


@pytest.mark.django_db
def test_job_status_returns_not_found_for_unknown_job(auth_client):
    """Redis connection error maps to 404."""
    with patch(
        "papadapi.events.views.asyncio.run", side_effect=RuntimeError("no redis")
    ):
        resp = auth_client.get("/api/v1/events/jobs/unknown-job/")
    assert resp.status_code == 404
    assert resp.data["status"] == "not_found"


@pytest.mark.django_db
def test_job_status_returns_status_for_known_job(auth_client):
    """When ARQ returns a status, it is forwarded in the response."""
    with patch("papadapi.events.views.asyncio.run", return_value="complete"):
        resp = auth_client.get("/api/v1/events/jobs/known-job-id/")
    assert resp.status_code == 200
    assert resp.data["status"] == "complete"
    assert resp.data["job_id"] == "known-job-id"
