import re

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from .models import UserProfile


_DIGIT_TRANSLATION = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def normalize_iranian_mobile(value):
    """Return an Iranian mobile number in 09xxxxxxxxx format, if valid."""
    value = str(value or "").translate(_DIGIT_TRANSLATION).strip()
    value = re.sub(r"[\s\-()]", "", value)

    if value.startswith("+98"):
        value = "0" + value[3:]
    elif value.startswith("0098"):
        value = "0" + value[4:]
    elif value.startswith("98"):
        value = "0" + value[2:]

    if re.fullmatch(r"09\d{9}", value):
        return value
    return None


def mobile_lookup_candidates(mobile):
    """Return common database representations for a normalized mobile."""
    local = mobile[1:]
    return {
        mobile,
        f"+98{local}",
        f"0098{local}",
        f"98{local}",
    }


def get_unique_profile_by_mobile(value):
    """Return one matching profile, or None for invalid/missing/duplicate values."""
    mobile = normalize_iranian_mobile(value)
    if not mobile:
        return None
    profiles = list(
        UserProfile.objects.select_related("user")
        .filter(mobile__in=mobile_lookup_candidates(mobile))[:2]
    )
    return profiles[0] if len(profiles) == 1 else None


class UsernameOrMobileBackend(ModelBackend):
    """Authenticate regular Django users by username or profile mobile."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        identifier = username or kwargs.get(UserModel.USERNAME_FIELD)
        if identifier is None or password is None:
            return None

        # An exact username always wins, avoiding ambiguous fallback behaviour.
        try:
            user = UserModel._default_manager.get_by_natural_key(identifier)
        except UserModel.DoesNotExist:
            user = None

        if user is None:
            profile = get_unique_profile_by_mobile(identifier)
            # A duplicated phone number must never select a user arbitrarily.
            if profile is not None:
                user = profile.user

        if user is not None:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        else:
            # Reduce timing differences between known and unknown identifiers.
            UserModel().set_password(password)

        return None
