"""Custom validators for Rubika bot models."""

from __future__ import annotations

import re
from typing import Optional

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_\-]{20,}$")


def validate_rubika_token(value: Optional[str]) -> None:
    """Ensure the configured Rubika bot token is syntactically valid."""
    if value in (None, ""):
        return
    if not _TOKEN_PATTERN.fullmatch(value):
        raise ValidationError(_("فرمت توکن روبیکا نامعتبر است."))

