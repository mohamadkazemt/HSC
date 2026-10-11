"""Database-aware async wrappers for long-lived Celery/Rubika workers."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, overload

from asgiref.sync import sync_to_async
from django.db import close_old_connections, connections

T = TypeVar("T")


@overload
def database_sync_to_async(func: Callable[..., T], **kwargs: Any) -> Any: ...


@overload
def database_sync_to_async(func: None = None, **kwargs: Any) -> Callable[[Callable[..., T]], Any]: ...


def database_sync_to_async(func: Callable[..., T] | None = None, **kwargs: Any) -> Any:
    """Run an ORM operation with connection cleanup on its owning thread."""

    kwargs["thread_sensitive"] = True

    def decorator(operation: Callable[..., T]) -> Any:
        @sync_to_async(**kwargs)
        def wrapped(*args: Any, **call_kwargs: Any) -> T:
            close_old_connections()
            try:
                return operation(*args, **call_kwargs)
            finally:
                close_old_connections()
                # The operation boundary is the safe point to release the
                # thread-owned connection even when CONN_MAX_AGE is zero.
                connections.close_all()

        return wraps(operation)(wrapped)

    return decorator(func) if func is not None else decorator
