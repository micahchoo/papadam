"""Tests for importexport async ARQ task functions."""

from unittest.mock import patch

import pytest

from papadapi.importexport.tasks import export_request_task, import_request_task


@pytest.mark.django_db(transaction=True)
async def test_export_request_task_delegates_to_sync(user):
    """export_request_task is an async wrapper: it calls the sync body via a thread."""
    with patch(
        "papadapi.importexport.tasks._export_sync", return_value=True
    ) as mock_sync:
        result = await export_request_task({}, 42)

    mock_sync.assert_called_once_with(42)
    assert result is True


@pytest.mark.django_db(transaction=True)
async def test_import_request_task_delegates_to_sync(user):
    """import_request_task is an async wrapper: it calls the sync body via a thread."""
    with patch(
        "papadapi.importexport.tasks._import_sync", return_value=True
    ) as mock_sync:
        result = await import_request_task({}, 99)

    mock_sync.assert_called_once_with(99)
    assert result is True


@pytest.mark.django_db(transaction=True)
async def test_export_request_task_propagates_exception(user):
    """Exceptions raised inside _export_sync surface from the async task."""
    with patch(
        "papadapi.importexport.tasks._export_sync",
        side_effect=ValueError("bad export"),
    ), pytest.raises(ValueError, match="bad export"):
        await export_request_task({}, 1)


@pytest.mark.django_db(transaction=True)
async def test_import_request_task_propagates_exception(user):
    """Exceptions raised inside _import_sync surface from the async task."""
    with patch(
        "papadapi.importexport.tasks._import_sync",
        side_effect=RuntimeError("bad import"),
    ), pytest.raises(RuntimeError, match="bad import"):
        await import_request_task({}, 2)
