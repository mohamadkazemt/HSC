from django.db.models.signals import post_save
from django.dispatch import receiver
from dashboard.models import Notification
from .tasks import send_rubika_message


@receiver(post_save, sender=Notification)
def send_notification_to_rubika(sender, instance: Notification, created, **kwargs):
    """
    ارسال نوتیفیکیشن به ربات روبیکا بعد از ایجاد
    شامل آیکون‌های مناسب و فرمت بهتر
    
    نوتیفیکیشن‌های درخواست تایید مرخصی که دکمه دارند از این signal نادیده گرفته می‌شوند
    چون آن‌ها با send_leave_approval_request task ارسال می‌شوند
    """
    if not created:
        return
    
    # نادیده گرفتن نوتیفیکیشن‌هایی که با دکمه ارسال می‌شوند
    if instance.title and ('درخواست جایگزینی' in instance.title or 'درخواست تایید' in instance.title):
        # این نوتیفیکیشن‌ها با send_leave_approval_request ارسال می‌شوند
        return
    
    user = instance.user
    profile = getattr(user, 'rubika_profile', None)
    
    # بررسی اینکه کاربر پروفایل روبیکا دارد و chat_id دارد
    if not profile or not profile.chat_id:
        return
    
    # انتخاب آیکون مناسب بر اساس نوع نوتیفیکیشن
    icons = {
        'info': 'ℹ️',
        'success': '✅',
        'warning': '⚠️',
        'error': '❌',
        'meeting': '📅',
    }
    icon = icons.get(instance.notification_type, 'ℹ️')
    
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
        message_lines.append('🔗 برای مشاهده جزئیات به پنل وب مراجعه کنید.')
    
    text = '\n'.join(message_lines)
    
    # ارسال پیام به ربات (async task)
    send_rubika_message.delay(profile.chat_id, text)

