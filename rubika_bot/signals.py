from django.db.models.signals import post_save
from django.dispatch import receiver
from dashboard.models import Notification
from .tasks import send_rubika_message
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Notification)
def send_notification_to_rubika(sender, instance: Notification, created, **kwargs):
    """
    ارسال نوتیفیکیشن به ربات روبیکا بعد از ایجاد
    شامل آیکون‌های مناسب و فرمت بهتر
    
    نوتیفیکیشن‌های درخواست تایید مرخصی که دکمه دارند از این signal نادیده گرفته می‌شوند
    چون آن‌ها با send_leave_approval_request task ارسال می‌شوند
    """
    logger.info(f"🔔 Signal triggered for notification {instance.id}, created={created}")
    
    if not created:
        logger.info(f"  ⏭️ Skipping - notification was updated, not created")
        return
    
    # نادیده گرفتن نوتیفیکیشن‌هایی که با دکمه ارسال می‌شوند
    # فقط این دو عنوان دقیق با دکمه ارسال می‌شوند (از leave_reports/utils.py)
    approval_titles_with_buttons = [
        'درخواست جایگزینی مرخصی',  # به جایگزین با دکمه تایید/رد
        'درخواست تأیید مرخصی',      # به مدیر با دکمه تایید/رد
    ]
    
    if instance.title and instance.title in approval_titles_with_buttons:
        logger.info(f"  ⏭️ Skipping - notification has approval buttons (title: {instance.title})")
        # این نوتیفیکیشن‌ها با send_leave_approval_request ارسال می‌شوند
        return
    
    user = instance.user
    profile = getattr(user, 'rubika_profile', None)
    
    logger.info(f"  👤 User: {user.username}, Has rubika_profile: {profile is not None}")
    
    # بررسی اینکه کاربر پروفایل روبیکا دارد و chat_id دارد
    if not profile or not profile.chat_id:
        logger.warning(f"  ❌ User {user.username} has no rubika profile or chat_id")
        return
    
    logger.info(f"  ✅ User has chat_id: {profile.chat_id}")
    
    # انتخاب آیکون مناسب بر اساس نوع نوتیفیکیشن و عنوان
    icons = {
        'info': 'ℹ️',
        'success': '✅',
        'warning': '⚠️',
        'error': '❌',
        'meeting': '📅',
    }
    icon = icons.get(instance.notification_type, 'ℹ️')
    
    # آیکون خاص برای چک‌لیست‌های برنامه‌ریزی شده
    if instance.title:
        title_lower = instance.title.lower()
        if 'چک‌لیست' in instance.title or 'checklist' in title_lower:
            if 'برنامه‌ریزی شده' in instance.title or 'scheduled' in title_lower:
                if instance.notification_type == 'warning':
                    icon = '⚠️📋'  # هشدار چک‌لیست برنامه‌ریزی شده
                else:
                    icon = '📋'  # چک‌لیست برنامه‌ریزی شده
            elif instance.notification_type == 'warning':
                icon = '⚠️📋'  # هشدار چک‌لیست
            elif instance.notification_type == 'success':
                icon = '✅📋'  # موفقیت چک‌لیست
            else:
                icon = '📋'  # چک‌لیست عادی
    
    # ساختن متن پیام
    message_lines = []
    
    # افزودن عنوان با آیکون
    if instance.title:
        message_lines.append(f'{icon} {instance.title}')
        message_lines.append('')
    
    # افزودن متن پیام
    message_lines.append(instance.message)
    
    # افزودن لینک در صورت وجود
    if instance.url:
        message_lines.append('')
        # برای چک‌لیست‌های برنامه‌ریزی شده، پیام خاص
        if instance.title and ('چک‌لیست برنامه‌ریزی شده' in instance.title or 'scheduled' in instance.title.lower()):
            message_lines.append('🔗 برای تکمیل چک‌لیست به پنل وب مراجعه کنید.')
        else:
            message_lines.append('🔗 برای مشاهده جزئیات به پنل وب مراجعه کنید.')
    
    text = '\n'.join(message_lines)
    
    logger.info(f"  📤 Sending message to rubika (chat_id: {profile.chat_id})")
    
    # ارسال پیام به ربات (async task)
    send_rubika_message.delay(profile.chat_id, text)
    
    logger.info(f"  ✅ Message queued successfully")


