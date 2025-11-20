import logging
from typing import Iterable, List, Optional

from django.contrib.auth.models import Group, User
from django.urls import reverse

from dashboard.models import Notification
from dashboard.notification_utils import safe_notification as _safe_notification


logger = logging.getLogger(__name__)


CHECKLIST_MANAGER_GROUPS = ['مدیر HSE']


def _notify_group_members(group_names: Iterable[str]) -> Iterable[User]:
    seen = set()
    for group_name in group_names:
        try:
            group = Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            logger.warning("Group '%s' not found for checklist notifications", group_name)
            continue

        for user in group.user_set.all():
            if user.id in seen:
                continue
            seen.add(user.id)
            yield user


def notify_checklist_failure(checklist, *, unacceptable_answers: List, actor: Optional[User] = None) -> None:
    """Notify responsible teams when a checklist contains unacceptable answers."""

    url = reverse('checklist_app:general_checklist_detail', args=[checklist.id]) if checklist.id else None
    answers_text = ', '.join(answer.question.text for answer in unacceptable_answers[:3])
    if len(unacceptable_answers) > 3:
        answers_text += ' و ...'

    message = (
        f'در چک‌لیست شماره {checklist.id} ({checklist.get_checklist_type_display()}) پاسخ غیرقابل قبولی ثبت شد. '
        f'نمونه سوالات: {answers_text}'
    )

    # Notify checklist submitter
    _safe_notification(
        user=checklist.user,
        title='هشدار چک‌لیست',
        message=message,
        notification_type='warning',
        url=url,
        actor=None,
        extra_log_context={'checklist_id': checklist.id, 'target': 'submitter'},
    )

    # Notify managers
    for user in _notify_group_members(CHECKLIST_MANAGER_GROUPS):
        _safe_notification(
            user=user,
            title='هشدار چک‌لیست',
            message=message,
            notification_type='warning',
            url=url,
            actor=actor,
            extra_log_context={'checklist_id': checklist.id, 'target_group': 'HSE'},
        )


def notify_checklist_success(checklist, *, actor: Optional[User] = None) -> None:
    """Optional confirmation notification for successful checklist submissions."""

    url = reverse('checklist_app:general_checklist_detail', args=[checklist.id]) if checklist.id else None
    message = f'چک‌لیست شماره {checklist.id} با موفقیت ثبت شد.'

    _safe_notification(
        user=checklist.user,
        title='ثبت چک‌لیست',
        message=message,
        notification_type='success',
        url=url,
        actor=None,
        extra_log_context={'checklist_id': checklist.id, 'target': 'submitter'},
    )
