import datetime
from django.utils import timezone
from django.urls import reverse
from shift_manager.utils import get_shift_for_date

def get_shift_for_date_and_time(date, time, work_group):
    """
    Determines the shift based on the date, time, and work group.
    For night shifts, it checks if the time is between 6 PM and 6 AM to assign the correct shift.
    """
    if 18 <= time.hour <= 23 or 0 <= time.hour < 6:
        # If the time is between 6 PM and 6 AM, consider it as the night shift
        shift_info = get_shift_for_date(date)
        return shift_info.get(work_group)
    else:
        # For other shifts, use the default logic
        shift_info = get_shift_for_date(date)
        return shift_info.get(work_group)


# ============= توابع کمکی نوتیفیکیشن =============

def send_notification_to_replacement(leave_request):
    """
    ارسال اعلان به جایگزین پیشنهادی برای تأیید درخواست مرخصی
    همراه با دکمه‌های تایید و رد در ربات روبیکا
    """
    from dashboard.models import Notification
    
    if leave_request.replacement_person:
        # بررسی نوع مرخصی برای متن مناسب
        leave_type_display = leave_request.get_leave_type_display()
        requester_name = leave_request.user.get_full_name() or leave_request.user.username
        
        # ایجاد URL برای نمایش جزئیات
        url = reverse('leave_reports:leave_detail', args=[leave_request.id])
        
        message = f'{requester_name} شما را به عنوان جایگزین برای {leave_type_display} در تاریخ {leave_request.shift_date} انتخاب کرده است.'
        title = 'درخواست جایگزینی مرخصی'
        
        # ارسال نوتیفیکیشن به داشبورد وب
        # این نوتیفیکیشن با عنوان "درخواست جایگزینی" در signal نادیده گرفته می‌شود
        # و فقط با send_leave_approval_request به ربات ارسال می‌شود
        Notification.objects.create(
            user=leave_request.replacement_person,
            title=title,
            message=message,
            notification_type='warning',  # هشدار برای نیاز به اقدام
            url=url
        )
        
        # ارسال پیام با دکمه‌های تایید/رد به ربات روبیکا
        send_leave_approval_notification_to_rubika(
            user=leave_request.replacement_person,
            leave_request=leave_request,
            approval_type='replacement'
        )


def send_notification_to_manager(leave_request):
    """
    ارسال اعلان به مدیر تأیید کننده برای تأیید نهایی درخواست مرخصی
    همراه با دکمه‌های تایید و رد در ربات روبیکا
    """
    from dashboard.models import Notification
    from .models import ApprovalHierarchy
    
    # پیدا کردن مدیر تأیید کننده
    requester_profile = getattr(leave_request.user, 'userprofile', None)
    if not requester_profile:
        return
    
    # بررسی سلسله مراتب تأیید
    hierarchy = None
    if requester_profile.part:
        # اول سلسله مراتب خاص Part را بررسی می‌کنیم
        hierarchy = ApprovalHierarchy.objects.filter(part=requester_profile.part).first()
        
        # اگر برای Part خاص تأیید کننده‌ای نبود، سلسله مراتب کلی Section را بررسی می‌کنیم
        if not hierarchy and requester_profile.section:
            hierarchy = ApprovalHierarchy.objects.filter(
                section=requester_profile.section, 
                part__isnull=True
            ).first()
    elif requester_profile.section:
        # فقط سلسله مراتب کلی Section را بررسی می‌کنیم
        hierarchy = ApprovalHierarchy.objects.filter(
            section=requester_profile.section, 
            part__isnull=True
        ).first()
    
    if hierarchy and hierarchy.approver and hierarchy.approver.user:
        manager = hierarchy.approver.user
        
        leave_type_display = leave_request.get_leave_type_display()
        requester_name = leave_request.user.get_full_name() or leave_request.user.username
        
        # ایجاد URL برای نمایش جزئیات
        url = reverse('leave_reports:leave_detail', args=[leave_request.id])
        
        message = f'درخواست {leave_type_display} {requester_name} برای تاریخ {leave_request.shift_date} منتظر تأیید نهایی شماست.'
        title = 'درخواست تأیید مرخصی'
        
        # ارسال نوتیفیکیشن به داشبورد وب
        Notification.objects.create(
            user=manager,
            title=title,
            message=message,
            notification_type='info',  # اطلاع‌رسانی
            url=url
        )
        
        # ارسال پیام با دکمه‌های تایید/رد به ربات روبیکا
        send_leave_approval_notification_to_rubika(
            user=manager,
            leave_request=leave_request,
            approval_type='manager'
        )


def send_notification_to_requester_approved(leave_request, approved_by_type='manager'):
    """
    ارسال اعلان به درخواست دهنده پس از تأیید درخواست
    
    Parameters:
    - leave_request: درخواست مرخصی
    - approved_by_type: نوع تأیید کننده ('replacement' یا 'manager')
    """
    from dashboard.models import Notification
    
    leave_type_display = leave_request.get_leave_type_display()
    
    # ایجاد URL برای نمایش جزئیات
    url = reverse('leave_reports:leave_detail', args=[leave_request.id])
    
    if approved_by_type == 'replacement':
        # تأیید توسط جایگزین
        approver_name = leave_request.replacement_person.get_full_name() or leave_request.replacement_person.username
        message = f'{approver_name} درخواست جایگزینی شما برای {leave_type_display} در تاریخ {leave_request.shift_date} را تأیید کرد. منتظر تأیید نهایی مدیر باشید.'
        title = 'تأیید جایگزینی مرخصی'
        notification_type = 'info'
    else:
        # تأیید نهایی توسط مدیر
        approver_name = leave_request.final_approver.user.get_full_name() or leave_request.final_approver.user.username if leave_request.final_approver else 'مدیر'
        message = f'درخواست {leave_type_display} شما برای تاریخ {leave_request.shift_date} توسط {approver_name} تأیید شد.'
        title = 'تأیید نهایی مرخصی'
        notification_type = 'success'
    
    Notification.objects.create(
        user=leave_request.user,
        title=title,
        message=message,
        notification_type=notification_type,
        url=url
    )


def send_notification_to_requester_rejected(leave_request, rejected_by_type='manager'):
    """
    ارسال اعلان به درخواست دهنده پس از رد درخواست
    
    Parameters:
    - leave_request: درخواست مرخصی
    - rejected_by_type: نوع رد کننده ('replacement' یا 'manager')
    """
    from dashboard.models import Notification
    
    leave_type_display = leave_request.get_leave_type_display()
    
    # ایجاد URL برای نمایش جزئیات
    url = reverse('leave_reports:leave_detail', args=[leave_request.id])
    
    if rejected_by_type == 'replacement':
        # رد توسط جایگزین
        rejector_name = leave_request.rejected_by.get_full_name() or leave_request.rejected_by.username if leave_request.rejected_by else 'جایگزین'
        message = f'{rejector_name} درخواست جایگزینی شما برای {leave_type_display} در تاریخ {leave_request.shift_date} را رد کرد.'
        if leave_request.rejection_reason:
            message += f' دلیل: {leave_request.rejection_reason}'
        title = 'رد جایگزینی مرخصی'
    else:
        # رد توسط مدیر
        rejector_name = leave_request.rejected_by.get_full_name() or leave_request.rejected_by.username if leave_request.rejected_by else 'مدیر'
        message = f'درخواست {leave_type_display} شما برای تاریخ {leave_request.shift_date} توسط {rejector_name} رد شد.'
        if leave_request.rejection_reason:
            message += f' دلیل: {leave_request.rejection_reason}'
        title = 'رد مرخصی'
    
    Notification.objects.create(
        user=leave_request.user,
        title=title,
        message=message,
        notification_type='error',  # خطا/رد
        url=url
    ) 


def send_leave_approval_notification_to_rubika(user, leave_request, approval_type='replacement'):
    """
    ارسال پیام با دکمه‌های تایید و رد به ربات روبیکا
    
    Parameters:
    - user: کاربری که باید پیام را دریافت کند (جایگزین یا مدیر)
    - leave_request: درخواست مرخصی
    - approval_type: نوع تایید ('replacement' یا 'manager')
    """
    import logging
    from rubika_bot.tasks import send_leave_approval_request
    
    logger = logging.getLogger(__name__)
    
    # بررسی اینکه کاربر پروفایل روبیکا دارد یا نه
    rubika_profile = getattr(user, 'rubika_profile', None)
    
    logger.info(f"🔍 Checking Rubika profile for user {user.username}")
    logger.info(f"   - Has rubika_profile: {rubika_profile is not None}")
    
    if not rubika_profile:
        logger.warning(f"⚠️ User {user.username} does not have a Rubika profile")
        return  # اگر کاربر در ربات نیست، فقط نوتیفیکیشن وب ارسال می‌شود
    
    logger.info(f"   - Chat ID: {rubika_profile.chat_id}")
    
    if not rubika_profile.chat_id:
        logger.warning(f"⚠️ User {user.username} has Rubika profile but no chat_id")
        return
    
    # ارسال پیام به ربات (async task)
    logger.info(f"📤 Sending leave approval request to Rubika bot")
    logger.info(f"   - Chat ID: {rubika_profile.chat_id}")
    logger.info(f"   - Leave ID: {leave_request.id}")
    logger.info(f"   - Approval Type: {approval_type}")
    
    try:
        # تلاش برای ارسال از طریق Celery
        result = send_leave_approval_request.delay(
            chat_id=rubika_profile.chat_id,
            leave_request_id=leave_request.id,
            approval_type=approval_type
        )
        logger.info(f"✅ Task queued successfully. Task ID: {result.id}")
    except Exception as e:
        # اگر Celery در دسترس نبود، به صورت مستقیم ارسال کن
        logger.warning(f"⚠️ Celery not available, sending synchronously: {str(e)}")
        try:
            send_leave_approval_request(
                chat_id=rubika_profile.chat_id,
                leave_request_id=leave_request.id,
                approval_type=approval_type
            )
            logger.info(f"✅ Message sent synchronously")
        except Exception as sync_error:
            logger.error(f"❌ Error sending synchronously: {str(sync_error)}", exc_info=True)
