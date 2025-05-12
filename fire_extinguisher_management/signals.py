from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import FireExtinguisher, ServiceRecord, Notification

User = get_user_model()


@receiver(post_save, sender=ServiceRecord)
def handle_service_record_notification(sender, instance, created, **kwargs):
    """
    Create notifications when a service record is created or updated.
    """
    if created:
        # Notify staff members about new service record
        staff_users = User.objects.filter(is_staff=True)
        message = f'سرویس جدید برای کپسول {instance.extinguisher.serial_tag} ثبت شد.'
        
        for user in staff_users:
            Notification.objects.create(
                user=user,
                message=message,
                url=f'/fire-extinguisher-management/extinguishers/{instance.extinguisher.pk}/'
            )


@receiver(post_save, sender=FireExtinguisher)
def handle_extinguisher_status_change(sender, instance, **kwargs):
    """
    Create notifications when a fire extinguisher's status changes.
    """
    if instance.status == 'needs_maintenance':
        # Notify staff members about maintenance needed
        staff_users = User.objects.filter(is_staff=True)
        message = f'کپسول {instance.serial_tag} نیاز به تعمیر و نگهداری دارد.'
        
        for user in staff_users:
            Notification.objects.create(
                user=user,
                message=message,
                url=f'/fire-extinguisher-management/extinguishers/{instance.pk}/'
            )
    
    elif instance.status == 'expired':
        # Notify staff members about expired extinguisher
        staff_users = User.objects.filter(is_staff=True)
        message = f'کپسول {instance.serial_tag} منقضی شده است.'
        
        for user in staff_users:
            Notification.objects.create(
                user=user,
                message=message,
                url=f'/fire-extinguisher-management/extinguishers/{instance.pk}/'
            ) 