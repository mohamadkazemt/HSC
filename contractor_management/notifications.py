import logging
from datetime import datetime
from typing import Iterable, Optional, Tuple

from django.contrib.auth.models import Group, User
from django.urls import reverse
from django.utils import timezone

from dashboard.models import Notification
from dashboard.notification_utils import safe_notification as _safe_notification


logger = logging.getLogger(__name__)


CONTRACTOR_MANAGER_GROUPS = ['مدیر HSE', 'مدیر پیمانکار']
EMPLOYEE_MANAGER_GROUPS = ['مدیر HSE', 'مدیر پیمانکار']
VEHICLE_MANAGER_GROUPS = ['مدیر HSE', 'مدیر پیمانکار']

WARNING_THRESHOLD_DAYS = 30


def _notify_group_members(group_names: Iterable[str]) -> Iterable[User]:
    seen = set()
    for group_name in group_names:
        try:
            group = Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            logger.warning("Group '%s' not found for contractor notifications", group_name)
            continue

        for user in group.user_set.all():
            if user.id in seen:
                continue
            seen.add(user.id)
            yield user


def _evaluate_expiry(expiry_date) -> Optional[Tuple[str, str, int]]:
    if not expiry_date:
        return None

    today = timezone.now().date()
    if isinstance(expiry_date, datetime):
        expiry_date = expiry_date.date()
    delta_days = (expiry_date - today).days

    if delta_days < 0:
        return 'error', 'expired', delta_days
    if delta_days <= WARNING_THRESHOLD_DAYS:
        return 'warning', 'upcoming', delta_days
    return None


def _collect_recipients(primary_user: Optional[User], group_names: Iterable[str]) -> Iterable[User]:
    seen = set()
    if primary_user:
        seen.add(primary_user.id)
        yield primary_user
    for user in _notify_group_members(group_names):
        if user.id in seen:
            continue
        seen.add(user.id)
        yield user


def notify_contractor_compliance(contractor, *, actor: Optional[User] = None) -> None:
    """Check contractor level deadlines and notify relevant stakeholders."""

    fields = [
        ('بیمه مسئولیت مدنی', contractor.liability_insurance_expiry),
        ('بیمه آتش‌سوزی', contractor.fire_insurance_expiry),
        ('صلاحیت پیمانکاری', contractor.contractor_certificate_expiry),
        ('صلاحیت ایمنی', contractor.safety_certificate_expiry),
    ]

    url = reverse('contractor_management:contractor_detail', args=[contractor.id])
    contractor_user = contractor.user if getattr(contractor, 'user', None) else None

    for label, expiry in fields:
        evaluation = _evaluate_expiry(expiry)
        if not evaluation:
            continue

        notification_type, status, delta = evaluation
        if status == 'expired':
            message = f'مدرک {label} پیمانکار {contractor.company_name} منقضی شده است.'
        else:
            message = f'مدرک {label} پیمانکار {contractor.company_name} در {abs(delta)} روز آینده منقضی می‌شود.'

        for user in _collect_recipients(contractor_user, CONTRACTOR_MANAGER_GROUPS):
            _safe_notification(
                user=user,
                title=f'انقضای {label} پیمانکار',
                message=message,
                notification_type=notification_type,
                url=url,
                actor=actor,
                context={'contractor_id': contractor.id, 'document': label, 'status': status},
            )


def notify_employee_compliance(employee, *, actor: Optional[User] = None) -> None:
    """Notify about employee document expirations."""

    evaluation = _evaluate_expiry(employee.entry_permit_expiration)
    if not evaluation:
        return

    contractor = employee.contractor
    url = reverse('contractor_management:data_management')
    contractor_user = contractor.user if getattr(contractor, 'user', None) else None
    notification_type, status, delta = evaluation

    if status == 'expired':
        message = f'مجوز ورود {employee.first_name} {employee.last_name} (پیمانکار {contractor.company_name}) منقضی شده است.'
    else:
        message = f'مجوز ورود {employee.first_name} {employee.last_name} (پیمانکار {contractor.company_name}) در {abs(delta)} روز آینده منقضی می‌شود.'

    for user in _collect_recipients(contractor_user, EMPLOYEE_MANAGER_GROUPS):
        _safe_notification(
            user=user,
            title='انقضای مجوز ورود پرسنل پیمانکار',
            message=message,
            notification_type=notification_type,
            url=url,
            actor=actor,
            context={'employee_id': employee.id, 'status': status},
        )


def notify_vehicle_compliance(vehicle, *, actor: Optional[User] = None) -> None:
    """Notify about vehicle compliance dates (insurance, inspection, permit)."""

    contractor = vehicle.contractor
    url = reverse('contractor_management:vehicle_detail', args=[vehicle.id]) if vehicle.id else reverse('contractor_management:data_management')
    contractor_user = contractor.user if getattr(contractor, 'user', None) else None

    fields = [
        ('بیمه خودرو', vehicle.insurance_expiry),
        ('معاینه فنی خودرو', vehicle.technical_inspection_expiry),
        ('مجوز تردد خودرو', vehicle.permit_expiry),
    ]

    for label, expiry in fields:
        evaluation = _evaluate_expiry(expiry)
        if not evaluation:
            continue

        notification_type, status, delta = evaluation
        if status == 'expired':
            message = f'{label} برای خودرو {vehicle.license_plate} (پیمانکار {contractor.company_name}) منقضی شده است.'
        else:
            message = f'{label} برای خودرو {vehicle.license_plate} (پیمانکار {contractor.company_name}) در {abs(delta)} روز آینده منقضی می‌شود.'

        for user in _collect_recipients(contractor_user, VEHICLE_MANAGER_GROUPS):
            _safe_notification(
                user=user,
                title=f'انقضای {label}',
                message=message,
                notification_type=notification_type,
                url=url,
                actor=actor,
                context={'vehicle_id': vehicle.id, 'document': label, 'status': status},
            )
