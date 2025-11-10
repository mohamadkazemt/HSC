import logging
from typing import Iterable, List, Optional

from django.contrib.auth.models import User
from django.urls import reverse

from accounts.models import UserProfile
from dashboard.models import Notification


logger = logging.getLogger(__name__)


ISSUE_OPTIONS = {'خیر', 'نامناسب', 'نیاز به تعمیر', 'خراب', 'غیرفعال'}


def _safe_notification(
    *,
    user: Optional[User],
    title: str,
    message: str,
    notification_type: str = 'info',
    url: Optional[str] = None,
    actor: Optional[User] = None,
    context: Optional[dict] = None,
) -> None:
    if not user:
        return

    if actor and actor == user:
        return

    try:
        Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            url=url,
        )
    except Exception as exc:  # pragma: no cover
        extra = context or {}
        extra.update({'user_id': getattr(user, 'id', None), 'title': title})
        logger.error("Failed to create machine checklist notification", exc_info=True, extra={'context': extra})


def _notify_shift_group_members(group_code: Optional[str]) -> Iterable[User]:
    if not group_code:
        return []

    profiles = UserProfile.objects.filter(group=group_code, user__is_active=True).select_related('user')
    return [profile.user for profile in profiles]


def notify_checklist_submission(checklist, *, issues: List, actor: Optional[User] = None) -> None:
    url = reverse('machine_checklist:checklist_detail', args=[checklist.id]) if checklist.id else None
    base_message = f'چک‌لیست ماشین {checklist.machine.workshop_code if checklist.machine else "نامشخص"} ثبت شد.'

    if issues:
        issue_messages = []
        for answer in issues[:3]:
            question_text = answer.question.text
            value = answer.selected_option or answer.answer_text or '—'
            issue_messages.append(f'{question_text}: {value}')
        if len(issues) > 3:
            issue_messages.append('...')
        issues_str = ' ؛ '.join(issue_messages)
        message = base_message + f' موارد نیازمند توجه: {issues_str}'
        notification_type = 'warning'
    else:
        message = base_message
        notification_type = 'info'

    # Notify submitter
    _safe_notification(
        user=checklist.user,
        title='ثبت چک‌لیست ماشین',
        message=message,
        notification_type='success' if not issues else 'warning',
        url=url,
        actor=None,
        context={'checklist_id': checklist.id, 'target': 'submitter'},
    )

    # Notify shift group members (e.g., supervisors)
    for user in _notify_shift_group_members(checklist.shift_group):
        _safe_notification(
            user=user,
            title='چک‌لیست ماشین جدید',
            message=message,
            notification_type=notification_type,
            url=url,
            actor=actor,
            context={'checklist_id': checklist.id, 'target_group': 'shift_group'},
        )
