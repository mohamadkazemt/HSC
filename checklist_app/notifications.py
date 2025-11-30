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


def notify_scheduled_checklist_created(instance, users: List[User]) -> None:
    """
    اطلاع‌رسانی به کاربران هنگام ایجاد چک‌لیست برنامه‌ریزی شده
    
    Args:
        instance: ScheduledChecklistInstance
        users: لیست کاربرانی که باید اطلاع دریافت کنند
    """
    from datetime import timedelta
    from django.utils import timezone
    
    url = reverse('checklist_app:general_checklist_form') + f'?scheduled_instance_id={instance.id}'
    
    # تعیین پیام بر اساس فاصله تا موعد
    today = timezone.now().date()
    days_until_due = (instance.due_date - today).days
    
    if days_until_due == 0:
        title = 'چک‌لیست برنامه‌ریزی شده - امروز'
        message = f'چک‌لیست "{instance.schedule.name}" برای امروز ({instance.due_date}) در انتظار تکمیل است.'
        notification_type = 'warning'
    elif days_until_due == 1:
        title = 'یادآوری چک‌لیست برنامه‌ریزی شده'
        message = f'چک‌لیست "{instance.schedule.name}" برای فردا ({instance.due_date}) در انتظار است.'
        notification_type = 'info'
    else:
        title = 'چک‌لیست برنامه‌ریزی شده ایجاد شد'
        message = f'چک‌لیست "{instance.schedule.name}" برای تاریخ {instance.due_date} ایجاد شد.'
        notification_type = 'info'
    
    for user in users:
        _safe_notification(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            url=url,
            actor=None,
            extra_log_context={
                'instance_id': instance.id,
                'schedule_id': instance.schedule.id,
                'due_date': str(instance.due_date),
                'target': 'scheduled_checklist_user'
            },
        )


def notify_pending_scheduled_checklists(user: User, pending_instances: List) -> None:
    """
    اطلاع‌رسانی به کاربر در مورد چک‌لیست‌های برنامه‌ریزی شده در انتظار
    
    Args:
        user: کاربر مورد نظر
        pending_instances: لیست ScheduledChecklistInstance های در انتظار
    """
    if not pending_instances:
        return
    
    from django.utils import timezone
    
    url = reverse('checklist_app:pending_scheduled_checklists')
    
    if len(pending_instances) == 1:
        instance = pending_instances[0]
        title = 'چک‌لیست برنامه‌ریزی شده در انتظار'
        message = f'چک‌لیست "{instance.schedule.name}" برای امروز در انتظار تکمیل است.'
    else:
        title = f'{len(pending_instances)} چک‌لیست برنامه‌ریزی شده در انتظار'
        checklist_names = ', '.join([inst.schedule.name for inst in pending_instances[:3]])
        if len(pending_instances) > 3:
            checklist_names += f' و {len(pending_instances) - 3} مورد دیگر'
        message = f'شما {len(pending_instances)} چک‌لیست برنامه‌ریزی شده برای امروز دارید: {checklist_names}'
    
    _safe_notification(
        user=user,
        title=title,
        message=message,
        notification_type='warning',
        url=url,
        actor=None,
        extra_log_context={
            'pending_count': len(pending_instances),
            'target': 'scheduled_checklist_user'
        },
    )


def notify_scheduled_checklist_due_soon(instance, users: List[User], days_before: int = 1) -> None:
    """
    اطلاع‌رسانی به کاربران چند روز قبل از موعد چک‌لیست برنامه‌ریزی شده
    
    Args:
        instance: ScheduledChecklistInstance
        users: لیست کاربرانی که باید اطلاع دریافت کنند
        days_before: چند روز قبل از موعد اطلاع داده شود (پیش‌فرض: 1 روز)
    """
    url = reverse('checklist_app:general_checklist_form') + f'?scheduled_instance_id={instance.id}'
    
    title = 'یادآوری چک‌لیست برنامه‌ریزی شده'
    message = f'چک‌لیست "{instance.schedule.name}" برای {days_before} روز دیگر ({instance.due_date}) در انتظار است.'
    
    for user in users:
        _safe_notification(
            user=user,
            title=title,
            message=message,
            notification_type='info',
            url=url,
            actor=None,
            extra_log_context={
                'instance_id': instance.id,
                'schedule_id': instance.schedule.id,
                'due_date': str(instance.due_date),
                'days_before': days_before,
                'target': 'scheduled_checklist_user'
            },
        )