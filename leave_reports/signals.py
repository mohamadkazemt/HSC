from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ShiftReport
from .utils import send_notification_to_replacement, send_notification_to_manager
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ShiftReport)
def leave_request_created(sender, instance, created, **kwargs):
    """
    سیگنال برای ارسال اعلان پس از ایجاد درخواست مرخصی
    """
    if created:  # فقط برای درخواست‌های جدید
        logger.info(f"🔔 Signal triggered for new leave request #{instance.id}")
        logger.info(f"   - User: {instance.user.username}")
        logger.info(f"   - Status: {instance.status}")
        logger.info(f"   - Replacement: {instance.replacement_person.username if instance.replacement_person else 'None'}")
        
        # ارسال اعلان به جایگزین یا مدیر بسته به وضعیت
        if instance.status == 'pending_replacement' and instance.replacement_person:
            # اگر نیاز به تأیید جایگزین داشت، به جایگزین اطلاع می‌دهیم
            logger.info(f"📤 Sending notification to replacement: {instance.replacement_person.username}")
            send_notification_to_replacement(instance)
            
        elif instance.status == 'pending_approval':
            # اگر مستقیم رفت به مدیر (مثل غیبت، استعلاجی)، به مدیر اطلاع می‌دهیم
            logger.info(f"📤 Sending notification to manager for approval")
            send_notification_to_manager(instance)
