from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import FireExtinguisher, ServiceRecord
from .notifications import notify_staff, build_extinguisher_url


@receiver(post_save, sender=ServiceRecord)
def handle_service_record_notification(sender, instance, created, **kwargs):
    """
    Create notifications when a service record is created or updated.
    """
    if created:
        # Notify staff members about new service record
        message = f'سرویس جدید برای کپسول {instance.extinguisher.serial_tag} ثبت شد.'
        notify_staff(
            title='ثبت سرویس کپسول',
            message=message,
            notification_type='info',
            url=build_extinguisher_url(instance.extinguisher),
        )


@receiver(post_save, sender=FireExtinguisher)
def handle_extinguisher_status_change(sender, instance, **kwargs):
    """
    Create notifications when a fire extinguisher's status changes.
    """
    if instance.status == 'needs_maintenance':
        # Notify staff members about maintenance needed
        message = f'کپسول {instance.serial_tag} نیاز به تعمیر و نگهداری دارد.'
        notify_staff(
            title='هشدار کپسول آتش‌نشانی',
            message=message,
            notification_type='warning',
            url=build_extinguisher_url(instance),
        )
    
    elif instance.status == 'expired':
        # Notify staff members about expired extinguisher
        message = f'کپسول {instance.serial_tag} منقضی شده است.'
        notify_staff(
            title='انقضای کپسول آتش‌نشانی',
            message=message,
            notification_type='error',
            url=build_extinguisher_url(instance),
        ) 