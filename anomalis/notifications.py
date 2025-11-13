import logging
from typing import Iterable, Optional

from django.contrib.auth.models import User
from django.urls import reverse

from dashboard.models import Notification


logger = logging.getLogger(__name__)


CRITICAL_PRIORITY_KEYWORDS = {'فوری', 'بحرانی', 'بحرانی ', 'critical', 'Critical', 'High', 'HIGH'}


def _safe_notification(
    *,
    user: Optional[User],
    title: str,
    message: str,
    notification_type: str = 'info',
    url: Optional[str] = None,
    actor: Optional[User] = None,
    extra_log_context: Optional[dict] = None,
    skip_actor_check: bool = False,  # برای مواردی که می‌خواهیم حتی به actor هم نتفیکیشن بدهیم
) -> None:
    """
    Helper to create a notification safely without breaking the flow.
    It skips notifications for anonymous/None users and avoids notifying
    the actor (the user who triggered the action) unless skip_actor_check=True.
    """

    if not user:
        logger.debug(f"Skipping notification: user is None (title: {title})")
        return

    if not skip_actor_check and actor and actor == user:
        logger.debug(f"Skipping notification: actor ({actor.username}) is the same as user ({user.username}) (title: {title})")
        return

    try:
        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            url=url,
        )
        logger.info(f"Notification created successfully: ID={notification.id}, user={user.username}, title={title}")
    except Exception as exc:  # pragma: no cover - defensive logging
        context = extra_log_context or {}
        context.update({'user_id': getattr(user, 'id', None), 'title': title})
        logger.error("Failed to create notification", exc_info=True, extra={'context': context})


def _notify_group_members(position_names: Iterable[str]) -> Iterable[User]:
    """Yield all users with the provided position names. Errors are logged but ignored."""

    seen_user_ids = set()
    from accounts.models import UserProfile
    
    for position_name in position_names:
        try:
            # جستجوی کاربران با سمت مشخص شده
            user_profiles = UserProfile.objects.filter(
                position__name=position_name,
                user__isnull=False
            ).select_related('user', 'position')
            
            for profile in user_profiles:
                if profile.user and profile.user.id not in seen_user_ids:
                    seen_user_ids.add(profile.user.id)
                    yield profile.user
        except Exception as e:
            logger.warning("Error finding users with position '%s': %s", position_name, str(e))
            continue


def _anomaly_url(anomaly) -> str:
    return reverse('anomalis:anomaly_detail', args=[anomaly.id])


def notify_anomaly_created(anomaly, *, actor: Optional[User] = None) -> None:
    """Send notifications after an anomaly is created."""

    url = _anomaly_url(anomaly)
    creator_name = anomaly.created_by.user.get_full_name() if anomaly.created_by and anomaly.created_by.user else 'سیستم'
    location_name = getattr(anomaly.location, 'name', 'محل نامشخص')

    # Follow-up officer
    followup_user = None
    if anomaly.followup:
        try:
            followup_user = anomaly.followup.user
        except AttributeError:
            logger.warning(f"Followup user not found for anomaly {anomaly.id}, followup={anomaly.followup}")
    
    if followup_user:
        # برای مسئول پیگیری، حتی اگر خودش آنومالی را ایجاد کرده باشد، نتفیکیشن ارسال می‌کنیم
        # چون باید از آنومالی که به او اختصاص داده شده مطلع شود
        _safe_notification(
            user=followup_user,
            title='آنومالی جدید برای پیگیری',
            message=f'آنومالی شماره {anomaly.id} در {location_name} برای پیگیری شما ثبت شد توسط {creator_name}.',
            notification_type='warning',
            url=url,
            actor=actor,
            skip_actor_check=True,  # حتی اگر خودش ایجاد کرده باشد، نتفیکیشن بده
            extra_log_context={'anomaly_id': anomaly.id, 'target': 'followup'},
        )
    else:
        logger.warning(f"Could not send notification to followup officer for anomaly {anomaly.id}: followup_user is None")

    # HSE managers
    for user in _notify_group_members(['مدیر HSE']):
        _safe_notification(
            user=user,
            title='ثبت آنومالی جدید',
            message=f'آنومالی شماره {anomaly.id} در {location_name} ثبت شد. مسئول پیگیری: {anomaly.followup}.',
            notification_type='info',
            url=url,
            actor=actor,
            extra_log_context={'anomaly_id': anomaly.id, 'target_group': 'مدیر HSE'},
        )

    # High priority escalation
    priority_value = getattr(anomaly.priority, 'priority', '')
    if priority_value:
        normalized_priority = priority_value.strip()
        if normalized_priority in CRITICAL_PRIORITY_KEYWORDS:
            for user in _notify_group_members(['مدیر HSE', 'بازرس شیفت ایمنی']):
                _safe_notification(
                    user=user,
                    title='🚨 آنومالی با اولویت بحرانی',
                    message=f'آنومالی بحرانی شماره {anomaly.id} در {location_name} ثبت شد.',
                    notification_type='error',
                    url=url,
                    actor=actor,
                    extra_log_context={'anomaly_id': anomaly.id, 'priority': normalized_priority},
                )


def notify_anomaly_status_changed(anomaly, *, actor: Optional[User] = None) -> None:
    """Notify creator and follow-up officer about status changes (action field)."""

    url = _anomaly_url(anomaly)
    status_text = 'ایمن' if anomaly.action else 'ناایمن'

    recipients = []
    if anomaly.created_by and anomaly.created_by.user:
        recipients.append((anomaly.created_by.user, 'ایجاد کننده'))
    if anomaly.followup and anomaly.followup.user:
        recipients.append((anomaly.followup.user, 'مسئول پیگیری'))

    for user, role in recipients:
        _safe_notification(
            user=user,
            title='تغییر وضعیت آنومالی',
            message=f'وضعیت آنومالی شماره {anomaly.id} به "{status_text}" تغییر یافت.',
            notification_type='success' if anomaly.action else 'warning',
            url=url,
            actor=actor,
            extra_log_context={'anomaly_id': anomaly.id, 'target_role': role},
        )


def notify_comment_created(comment, *, actor: Optional[User] = None) -> None:
    """Notify related users when a new comment is added to an anomaly."""

    anomaly = comment.anomaly
    url = _anomaly_url(anomaly)
    commenter_name = comment.user.user.get_full_name() if comment.user and comment.user.user else 'یک کاربر'

    targets = []

    # Notify anomaly creator
    if anomaly.created_by and anomaly.created_by.user:
        targets.append((anomaly.created_by.user, 'ایجاد کننده'))

    # Notify follow-up officer
    if anomaly.followup and anomaly.followup.user:
        targets.append((anomaly.followup.user, 'مسئول پیگیری'))

    # Notify parent comment owner for replies
    if comment.parent and comment.parent.user and comment.parent.user.user:
        targets.append((comment.parent.user.user, 'نویسنده کامنت والد'))

    for user, role in targets:
        _safe_notification(
            user=user,
            title='کامنت جدید روی آنومالی',
            message=f'{commenter_name} برای آنومالی شماره {anomaly.id} کامنت ثبت کرد.',
            notification_type='info',
            url=url,
            actor=actor,
            extra_log_context={'anomaly_id': anomaly.id, 'target_role': role, 'comment_id': comment.id},
        )


def notify_anomaly_approval_request(anomaly, *, actor: Optional[User] = None) -> None:
    """Notify the designated approver that an anomaly awaits approval."""

    if not anomaly.approved_by:
        return

    url = _anomaly_url(anomaly)
    requester_name = anomaly.requested_by.get_full_name() if anomaly.requested_by else 'یکی از کاربران'

    _safe_notification(
        user=anomaly.approved_by,
        title='درخواست تأیید آنومالی',
        message=f'{requester_name} درخواست تأیید آنومالی شماره {anomaly.id} را ارسال کرده است.',
        notification_type='warning',
        url=url,
        actor=actor,
        extra_log_context={'anomaly_id': anomaly.id, 'target': 'approver'},
    )


def notify_request_safe_assignment(officer_user: Optional[User], anomaly, *, actor: Optional[User] = None) -> None:
    """Notify shift safety inspector that a safe request is pending."""

    if not officer_user:
        return

    url = _anomaly_url(anomaly)
    requester_name = officer_user.get_full_name() if actor is None else actor.get_full_name()

    _safe_notification(
        user=officer_user,
        title='درخواست ایمن‌سازی آنومالی',
        message=f'آنومالی شماره {anomaly.id} برای بررسی وضعیت ایمنی به شما ارجاع شد توسط {requester_name}.',
        notification_type='warning',
        url=url,
        actor=actor,
        extra_log_context={'anomaly_id': anomaly.id, 'target': 'officer'},
    )


def notify_safe_result(anomaly, *, approved: bool, actor: Optional[User] = None) -> None:
    """Notify follow-up and creator about approval/rejection results."""

    url = _anomaly_url(anomaly)
    title = 'تأیید ایمن بودن آنومالی' if approved else 'رد ایمن بودن آنومالی'
    message = (
        f'آنومالی شماره {anomaly.id} به وضعیت ایمن تغییر یافت.' if approved
        else f'درخواست ایمن بودن آنومالی شماره {anomaly.id} رد شد.'
    )
    notification_type = 'success' if approved else 'error'

    targets = []
    if anomaly.followup and anomaly.followup.user:
        targets.append((anomaly.followup.user, 'مسئول پیگیری'))
    if anomaly.created_by and anomaly.created_by.user:
        targets.append((anomaly.created_by.user, 'ایجاد کننده'))

    for user, role in targets:
        _safe_notification(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            url=url,
            actor=actor,
            extra_log_context={'anomaly_id': anomaly.id, 'target_role': role},
        )
