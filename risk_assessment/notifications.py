import logging
from typing import Iterable, Optional

from django.contrib.auth.models import Group, User
from django.urls import reverse

from dashboard.models import Notification
from dashboard.notification_utils import safe_notification as _safe_notification


logger = logging.getLogger(__name__)


RISK_MANAGER_GROUPS = ['مدیر HSE']


def _notify_group_members(group_names: Iterable[str]) -> Iterable[User]:
    """دریافت کاربران عضو گروه‌های مشخص شده"""
    seen_ids = set()
    for group_name in group_names:
        try:
            group = Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            logger.warning("Group '%s' not found for risk assessment notifications", group_name)
            continue

        for user in group.user_set.all():
            if user.id in seen_ids:
                continue
            seen_ids.add(user.id)
            yield user


def _risk_url(risk) -> str:
    """دریافت URL جزئیات ریسک"""
    return reverse('risk_assessment:risk_detail', args=[risk.id])


def _risk_approval_url(risk) -> str:
    """دریافت URL صفحه تأیید ریسک"""
    return reverse('risk_assessment:risk_approve', args=[risk.id])


def notify_risk_created(risk, *, actor: Optional[User] = None) -> None:
    """ارسال اعلان به مدیر HSE برای تأیید ریسک جدید"""
    
    url = _risk_approval_url(risk)
    position_name = risk.position.name if risk.position else 'نامشخص'
    activity = risk.activity_component[:50] if risk.activity_component else 'نامشخص'
    
    title = 'ریسک جدید نیاز به تأیید'
    message = (
        f'ریسک جدید برای شغل "{position_name}" - فعالیت "{activity}" '
        f'با عدد ریسک {risk.risk_number} ({risk.get_risk_level_display_fa()}) ثبت شد و نیاز به تأیید دارد.'
    )
    
    notification_type = 'warning' if risk.risk_level == 'High' else 'info'
    
    for user in _notify_group_members(RISK_MANAGER_GROUPS):
        _safe_notification(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            url=url,
            actor=actor,
            extra_log_context={'risk_id': risk.id, 'risk_number': risk.risk_number},
        )
    
    # اعلان به ایجادکننده
    author_user = risk.created_by.user if risk.created_by else None
    if author_user:
        _safe_notification(
            user=author_user,
            title='ریسک ثبت شد',
            message=f'ریسک شما با عدد ریسک {risk.risk_number} ثبت شد و در انتظار تأیید مدیر HSE است.',
            notification_type='success',
            url=_risk_url(risk),
            actor=None,
            extra_log_context={'risk_id': risk.id, 'target': 'author'},
        )


def notify_risk_approved(risk, *, actor: Optional[User] = None) -> None:
    """ارسال اعلان به ایجادکننده پس از تأیید ریسک"""
    
    url = _risk_url(risk)
    approver_name = risk.approved_by.user.get_full_name() if risk.approved_by and risk.approved_by.user else 'مدیر HSE'
    
    # اعلان به ایجادکننده
    author_user = risk.created_by.user if risk.created_by else None
    if author_user:
        _safe_notification(
            user=author_user,
            title='ریسک تأیید شد',
            message=f'ریسک شما با عدد ریسک {risk.risk_number} توسط {approver_name} تأیید شد.',
            notification_type='success',
            url=url,
            actor=actor,
            extra_log_context={'risk_id': risk.id, 'target': 'author'},
        )


def notify_risk_rejected(risk, *, actor: Optional[User] = None) -> None:
    """ارسال اعلان به ایجادکننده پس از رد ریسک"""
    
    url = _risk_url(risk)
    rejector_name = risk.rejected_by.user.get_full_name() if risk.rejected_by and risk.rejected_by.user else 'مدیر HSE'
    reason = risk.rejection_reason[:100] if risk.rejection_reason else 'دلیل ذکر نشده'
    
    # اعلان به ایجادکننده
    author_user = risk.created_by.user if risk.created_by else None
    if author_user:
        _safe_notification(
            user=author_user,
            title='ریسک رد شد',
            message=f'ریسک شما با عدد ریسک {risk.risk_number} توسط {rejector_name} رد شد. دلیل: {reason}',
            notification_type='error',
            url=url,
            actor=actor,
            extra_log_context={'risk_id': risk.id, 'target': 'author'},
        )

