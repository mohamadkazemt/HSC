"""Thin HTTP client for the PeyamHub messenger service (https://peyamhub.ir).

PeyamHub exposes ``POST /api/v1/send`` authenticated with
``Authorization: Bearer <key>``. Targets may be a phone number (``+98...``,
resolved against the connected Rubika account's contact book), an
``@username`` or a Rubika GUID. The API key is bound server-side to one
connected account, so callers only need key + target + text.
"""

import logging

import requests

from django.conf import settings

logger = logging.getLogger(__name__)


class PeyamHubError(Exception):
    """Raised when PeyamHub could not be reached or rejected the message."""

    def __init__(self, message, *, status_code=None):
        self.status_code = status_code
        super().__init__(message)


def _config():
    base_url = getattr(settings, "PEYAMHUB_BASE_URL", "").rstrip("/")
    api_key = getattr(settings, "PEYAMHUB_API_KEY", "")
    timeout = getattr(settings, "PEYAMHUB_TIMEOUT", 20)
    if not base_url or not api_key:
        raise PeyamHubError("تنظیمات PEYAMHUB_BASE_URL / PEYAMHUB_API_KEY کامل نیست.")
    return base_url, api_key, timeout


def normalize_phone(mobile):
    """Normalize a local Iranian mobile number to E.164 (+98...) for PeyamHub."""
    if not mobile:
        return ""
    digits = "".join(ch for ch in str(mobile).strip() if ch.isdigit())
    if digits.startswith("0098"):
        digits = digits[4:]
    elif digits.startswith("98") and len(digits) == 12:
        digits = digits[2:]
    elif digits.startswith("0"):
        digits = digits[1:]
    if len(digits) == 10 and digits.startswith("9"):
        return f"+98{digits}"
    return ""


def send_message(target, text):
    """Send one message; returns the PeyamHub log payload on success.

    Raises PeyamHubError with a user-presentable Persian message on failure.
    """
    base_url, api_key, timeout = _config()
    try:
        response = requests.post(
            f"{base_url}/api/v1/send",
            json={"target": target, "text": text},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )
    except requests.RequestException as exc:
        logger.warning("PeyamHub unreachable: %s", exc)
        raise PeyamHubError("سرویس پیام‌رسان در دسترس نیست.") from exc

    payload = {}
    try:
        payload = response.json()
    except ValueError:
        pass

    if response.status_code != 200:
        error = payload.get("error") or payload.get("detail") or f"HTTP {response.status_code}"
        raise PeyamHubError(str(error), status_code=response.status_code)

    if payload.get("status") != "ok":
        raise PeyamHubError(payload.get("error") or "ارسال پیام ناموفق بود.", status_code=422)

    return payload
