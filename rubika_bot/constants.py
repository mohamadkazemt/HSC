"""Centralised configuration helpers for the Rubika bot integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Tuple

from django.conf import settings


@dataclass(frozen=True)
class _BotDefaults:
    """Fallback values for Rubika bot configuration."""

    max_users_per_page: int = 200
    connection_code_ttl_minutes: int = 60
    log_cleanup_days: int = 7
    webhook_rate_limit: str = "180/m"
    webhook_allowed_ips: Tuple[str, ...] = ()
    bot_request_timeout: float = 15.0
    deeplink_template: str = "https://rubika.ir/{bot_username}?start={code}"


_DEFAULTS = _BotDefaults()


def _get(name: str, default: Any) -> Any:
    config = getattr(settings, "RUBIKA_BOT", {}) or {}
    return config.get(name, default)


MAX_USERS_PER_PAGE: int = int(
    _get("MAX_USERS_PER_PAGE", _DEFAULTS.max_users_per_page)
)
CONNECTION_CODE_TTL_MINUTES: int = int(
    _get("CONNECTION_CODE_TTL_MINUTES", _DEFAULTS.connection_code_ttl_minutes)
)
LOG_CLEANUP_DAYS: int = int(_get("LOG_CLEANUP_DAYS", _DEFAULTS.log_cleanup_days))
WEBHOOK_RATE_LIMIT: str = str(_get("WEBHOOK_RATE_LIMIT", _DEFAULTS.webhook_rate_limit))
WEBHOOK_ALLOWED_IPS: Tuple[str, ...] = tuple(
    _get("WEBHOOK_ALLOWED_IPS", _DEFAULTS.webhook_allowed_ips)
    or ()
)
BOT_REQUEST_TIMEOUT: float = float(
    _get("BOT_REQUEST_TIMEOUT", _DEFAULTS.bot_request_timeout)
)
DEEPLINK_TEMPLATE: str = str(
    _get("DEEPLINK_TEMPLATE", _DEFAULTS.deeplink_template)
)


def is_ip_allowed(ip: str) -> bool:
    """Check whether a client IP is allowed to call the webhook endpoint."""
    if not WEBHOOK_ALLOWED_IPS:
        return True
    return ip in WEBHOOK_ALLOWED_IPS


def as_debug_tuple() -> Iterable[Tuple[str, Any]]:
    """Return the effective configuration as a tuple list (useful for logging)."""
    return (
        ("MAX_USERS_PER_PAGE", MAX_USERS_PER_PAGE),
        ("CONNECTION_CODE_TTL_MINUTES", CONNECTION_CODE_TTL_MINUTES),
        ("LOG_CLEANUP_DAYS", LOG_CLEANUP_DAYS),
        ("WEBHOOK_RATE_LIMIT", WEBHOOK_RATE_LIMIT),
        ("WEBHOOK_ALLOWED_IPS", WEBHOOK_ALLOWED_IPS),
        ("BOT_REQUEST_TIMEOUT", BOT_REQUEST_TIMEOUT),
        ("DEEPLINK_TEMPLATE", DEEPLINK_TEMPLATE),
    )

