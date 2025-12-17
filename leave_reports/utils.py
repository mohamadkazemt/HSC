import datetime
from django.utils import timezone
from django.urls import reverse
from shift_manager.utils import get_shift_for_date
from .models import ApprovalHierarchy

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


def get_approver_for_user_profile(user_profile):
    """
    پیدا کردن تأیید کننده مرخصی برای یک UserProfile بر اساس بهترین تطبیق با قوانین ApprovalHierarchy
    
    Parameters:
    - user_profile: UserProfile که می‌خواهیم تأییدکننده آن را پیدا کنیم
    
    Returns:
    - UserProfile: تأییدکننده مرخصی یا None اگر تأییدکننده‌ای پیدا نشد
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if not user_profile:
        return None
    
    user = user_profile.user
    logger.info(f"🔍 Finding approver for user: {user.username} (ID: {user.id})")
    logger.info(f"   Profile: group={user_profile.group}, section={user_profile.section}, "
               f"part={user_profile.part}, unit_group={user_profile.unit_group}, "
               f"position={user_profile.position}")
    
    # پیدا کردن همه قوانینی که با پروفایل کاربر تطبیق دارند
    matching_rules = []
    
    all_rules = ApprovalHierarchy.objects.select_related(
        'approver', 'approver__user', 'section', 'part', 'unit_group', 'position'
    ).prefetch_related('specific_users').all()
    
    logger.info(f"   Total rules to check: {all_rules.count()}")
    
    for rule in all_rules:
        # بررسی تطبیق
        matches = rule.matches_user_profile(user_profile)
        logger.info(f"   Rule {rule.id}: matches={matches}, approver={rule.approver}")
        
        if matches:
            criteria_count = rule.get_criteria_count()
            weight = rule.get_weight()
            matching_rules.append((criteria_count, weight, rule))
            logger.info(f"   ✅ Rule {rule.id} matched! (criteria_count: {criteria_count}, weight: {weight})")
        else:
            # بررسی جزئی‌تر چرا تطبیق نکرد
            if rule._has_specific_users():
                specific_user_ids = list(rule.specific_users.values_list('id', flat=True))
                logger.info(f"   ❌ Rule {rule.id} didn't match - specific_users: {specific_user_ids}, user_id: {user.id}, user in list: {user.id in specific_user_ids}")
            if rule.work_group:
                logger.info(f"   ❌ Rule {rule.id} - work_group check: rule={rule.work_group}, profile={user_profile.group}")
            if rule.section:
                logger.info(f"   ❌ Rule {rule.id} - section check: rule={rule.section.id if rule.section else None}, profile={user_profile.section.id if user_profile.section else None}")
            if rule.part:
                logger.info(f"   ❌ Rule {rule.id} - part check: rule={rule.part.id if rule.part else None}, profile={user_profile.part.id if user_profile.part else None}")
            if rule.unit_group:
                logger.info(f"   ❌ Rule {rule.id} - unit_group check: rule={rule.unit_group.id if rule.unit_group else None}, profile={user_profile.unit_group.id if user_profile.unit_group else None}")
            if rule.position:
                logger.info(f"   ❌ Rule {rule.id} - position check: rule={rule.position.id if rule.position else None}, profile={user_profile.position.id if user_profile.position else None}")
    
    if not matching_rules:
        logger.warning(f"⚠️ No matching approval rule found for user {user.username}")
        return None
    
    # مرتب‌سازی: اول بر اساس تعداد معیارها (نزولی)، سپس بر اساس وزن (نزولی)
    # قانون با بیشترین معیار و در صورت تساوی، با بالاترین وزن اولویت دارد
    matching_rules.sort(key=lambda x: (x[0], x[1]), reverse=True)
    
    # برگرداندن تأیید کننده از قانون با بیشترین معیار و بالاترین وزن
    best_rule = matching_rules[0][2]
    logger.info(f"✅ Best matching rule: {best_rule.id} (criteria_count: {matching_rules[0][0]}, weight: {matching_rules[0][1]})")
    logger.info(f"   Approver: {best_rule.approver}")
    
    return best_rule.approver


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
    از متد get_required_approver() برای پیدا کردن تأیید کننده استفاده می‌کند
    """
    import logging
    from dashboard.models import Notification
    
    logger = logging.getLogger(__name__)
    
    logger.info(f"📤 send_notification_to_manager called for leave request #{leave_request.id}")
    
    # استفاده از متد جدید برای پیدا کردن تأیید کننده
    approver_profile = leave_request.get_required_approver()
    
    if not approver_profile:
        logger.warning(f"⚠️ No approver found for leave request #{leave_request.id}")
        return
    
    if not approver_profile.user:
        logger.warning(f"⚠️ Approver profile has no associated user")
        return
    
    manager = approver_profile.user
    logger.info(f"✅ Manager found: {manager.username} (profile: {approver_profile})")
    
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
    logger.info(f"📲 Calling send_leave_approval_notification_to_rubika for manager")
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
