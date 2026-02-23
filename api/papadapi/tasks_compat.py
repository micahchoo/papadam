"""
ARQ migration shim — Phase 1a

Replaces Huey's @db_task() and @task() decorators so Huey can be fully
removed as a dependency while the existing task functions continue to work
synchronously. In Phase 1c each task will be rewritten as a proper async
ARQ job and this shim will be deleted.

Usage in task modules:
    from papadapi.tasks_compat import db_task, task
"""

import functools
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def _make_shim(func: F) -> F:
    """Wrap func so it has a .schedule() method that calls it synchronously."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    def schedule(args: tuple = (), delay: int = 0, **_: Any) -> Any:  # noqa: ARG001
        return func(*args)

    wrapper.schedule = schedule  # type: ignore[attr-defined]
    wrapper.call_local = func  # type: ignore[attr-defined]
    return wrapper  # type: ignore[return-value]


def db_task(*args: Any, **_kwargs: Any) -> Any:
    """Shim for huey.contrib.djhuey.db_task."""
    if len(args) == 1 and callable(args[0]):
        return _make_shim(args[0])

    def decorator(func: F) -> F:
        return _make_shim(func)

    return decorator


def task(*args: Any, retries: int = 0, retry_delay: int = 0, **_kwargs: Any) -> Any:
    """Shim for huey.contrib.djhuey.task."""
    if len(args) == 1 and callable(args[0]):
        return _make_shim(args[0])

    def decorator(func: F) -> F:
        return _make_shim(func)

    return decorator
