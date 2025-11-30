"""
Helper functions for scheduled checklist enforcement system
"""
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, datetime
from django.db import transaction
from accounts.models import UserProfile
from shift_manager.utils import get_shift_for_date, get_active_groups_for_current_shift
from .models import ChecklistSchedule, ScheduledChecklistInstance


def get_users_on_shift(target_date: date, shift_name: str = 'روزکار اول'):
    """
    دریافت لیست کاربران (بازرسان ایمنی) که در شیفت مشخص شده در تاریخ مشخص کار می‌کنند.
    
    Args:
        target_date: تاریخ مورد نظر
        shift_name: نام شیفت (مثلاً 'روزکار اول')
    
    Returns:
        QuerySet of User objects who are Safety Inspectors on the specified shift
    """
    # دریافت شیفت‌های تمام گروه‌ها در تاریخ مشخص
    shifts = get_shift_for_date(target_date)
    
    # پیدا کردن گروه‌هایی که در شیفت مشخص شده کار می‌کنند
    active_groups = []
    for group, group_shift in shifts.items():
        # بررسی هم 'اول' و هم 'دوم' برای هر شیفت
        # تبدیل نام شیفت برای تطابق (مثلاً 'روزکار اول' با 'روزکار دوم')
        shift_variations = [shift_name]
        if 'اول' in shift_name:
            shift_variations.append(shift_name.replace('اول', 'دوم'))
        elif 'دوم' in shift_name:
            shift_variations.append(shift_name.replace('دوم', 'اول'))
        
        if group_shift in shift_variations and 'OFF' not in group_shift:
            active_groups.append(group)
    
    # دریافت بازرسان ایمنی از گروه‌های فعال
    safety_inspectors = User.objects.filter(
        userprofile__group__in=active_groups,
        userprofile__position__name='بازرس شیفت ایمنی',
        is_active=True
    ).select_related('userprofile', 'userprofile__position').distinct()
    
    return safety_inspectors


def get_pending_scheduled_checklists(user: User, target_date: date = None):
    """
    دریافت لیست چک‌لیست‌های برنامه‌ریزی شده در انتظار برای کاربر
    
    Args:
        user: کاربر مورد نظر
        target_date: تاریخ مورد نظر (پیش‌فرض: امروز)
    
    Returns:
        QuerySet of ScheduledChecklistInstance objects
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if target_date is None:
        target_date = timezone.now().date()
    
    # دریافت گروه کاری کاربر
    try:
        user_profile = user.userprofile
        user_group = user_profile.group
        user_position = user_profile.position
    except UserProfile.DoesNotExist:
        logger.debug(f"User {user.id} has no UserProfile")
        return ScheduledChecklistInstance.objects.none()
    
    # بررسی اینکه کاربر بازرس شیفت ایمنی است
    if not user_position or user_position.name != 'بازرس شیفت ایمنی':
        logger.debug(f"User {user.id} is not a Safety Inspector (position: {user_position.name if user_position else 'None'})")
        return ScheduledChecklistInstance.objects.none()
    
    # دریافت شیفت کاربر در تاریخ مشخص
    shifts = get_shift_for_date(target_date, user_profile)
    user_shift = shifts.get('user_group_shift')
    
    # اگر کاربر در شیفت روزکار نیست، چک‌لیست برنامه‌ریزی شده ندارد
    if not user_shift or 'روزکار' not in user_shift:
        logger.debug(f"User {user.id} is not on day shift (shift: {user_shift})")
        return ScheduledChecklistInstance.objects.none()
    
    # دریافت چک‌لیست‌های برنامه‌ریزی شده در انتظار
    pending_instances = ScheduledChecklistInstance.objects.filter(
        status='pending',
        due_date=target_date,
        schedule__is_active=True
    ).select_related('schedule').prefetch_related(
        'schedule__target_machine',
        'schedule__target_location_section',
        'schedule__target_contractor_vehicle'
    )
    
    logger.debug(f"Found {pending_instances.count()} pending checklists for user {user.id} on {target_date}")
    return pending_instances


def check_pending_tasks(user: User, target_date: date = None):
    """
    بررسی وجود چک‌لیست‌های برنامه‌ریزی شده در انتظار برای کاربر
    
    Args:
        user: کاربر مورد نظر
        target_date: تاریخ مورد نظر (پیش‌فرض: امروز)
    
    Returns:
        tuple: (has_pending, pending_list, error_message)
        - has_pending: True اگر چک‌لیست در انتظار وجود دارد
        - pending_list: لیست چک‌لیست‌های در انتظار
        - error_message: پیام خطا در صورت وجود
    """
    if target_date is None:
        target_date = timezone.now().date()
    
    try:
        pending_instances = get_pending_scheduled_checklists(user, target_date)
        pending_list = list(pending_instances)
        
        if pending_list:
            checklist_names = [f"{inst.schedule.name} ({inst.due_date})" for inst in pending_list]
            error_message = (
                f"قبل از ثبت گزارش روزانه، باید چک‌لیست‌های برنامه‌ریزی شده زیر تکمیل شوند:\n"
                f"{chr(10).join(f'- {name}' for name in checklist_names)}"
            )
            return True, pending_list, error_message
        
        return False, [], None
    
    except Exception as e:
        error_message = f"خطا در بررسی چک‌لیست‌های در انتظار: {str(e)}"
        return True, [], error_message


def create_scheduled_instances_for_date(target_date: date = None):
    """
    ایجاد نمونه‌های چک‌لیست برنامه‌ریزی شده برای تاریخ مشخص
    
    این تابع باید به صورت روزانه (مثلاً با cron job) اجرا شود
    تا نمونه‌های جدید برای تاریخ‌های آینده ایجاد شوند.
    
    Args:
        target_date: تاریخ مورد نظر (پیش‌فرض: امروز)
    """
    if target_date is None:
        target_date = timezone.now().date()
    
    active_schedules = ChecklistSchedule.objects.filter(is_active=True)
    
    for schedule in active_schedules:
        should_create = False
        
        if schedule.schedule_type == 'monthly_days':
            # بررسی آیا امروز یکی از روزهای مشخص شده ماه است
            if target_date.day in schedule.monthly_days:
                should_create = True
        
        elif schedule.schedule_type == 'specific_dates':
            # بررسی آیا امروز یکی از تاریخ‌های مشخص شده است
            date_str = target_date.strftime('%Y-%m-%d')
            if date_str in schedule.specific_dates:
                should_create = True
        
        elif schedule.schedule_type == 'weekly':
            # برای هفتگی، می‌توانید منطق خاص خود را اضافه کنید
            # مثلاً هر دوشنبه
            if target_date.weekday() == 0:  # Monday
                should_create = True
        
        if should_create:
            # ایجاد نمونه برای هر هدف (چندین ماشین/مکان)
            targets = []
            
            if schedule.checklist_type == 'machine':
                # استفاده از target_machines (جدید) یا target_machine (قدیمی)
                if schedule.target_machines:
                    from BaseInfo.models import MiningMachine
                    targets = MiningMachine.objects.filter(id__in=schedule.target_machines)
                elif schedule.target_machine:
                    targets = [schedule.target_machine]
            
            elif schedule.checklist_type == 'location':
                # استفاده از target_location_sections (جدید) یا target_location_section (قدیمی)
                if schedule.target_location_sections:
                    from anomalis.models import LocationSection
                    targets = LocationSection.objects.filter(id__in=schedule.target_location_sections)
                elif schedule.target_location_section:
                    targets = [schedule.target_location_section]
            
            elif schedule.checklist_type == 'contractor_vehicle':
                # استفاده از target_contractor_vehicles (جدید) یا target_contractor_vehicle (قدیمی)
                if schedule.target_contractor_vehicles:
                    from contractor_management.models import Vehicle
                    targets = Vehicle.objects.filter(id__in=schedule.target_contractor_vehicles)
                elif schedule.target_contractor_vehicle:
                    targets = [schedule.target_contractor_vehicle]
            
            # ایجاد نمونه برای هر هدف
            for target in targets:
                ScheduledChecklistInstance.objects.get_or_create(
                    schedule=schedule,
                    due_date=target_date,
                    defaults={'status': 'pending'}
                )


def create_instances_for_schedule(schedule):
    """
    ایجاد نمونه‌های چک‌لیست برای یک schedule خاص
    
    این تابع برای schedule های با نوع specific_dates، instances را برای تمام تاریخ‌های مشخص شده ایجاد می‌کند.
    برای monthly_days و weekly، instances را برای تاریخ‌های آینده (تا 30 روز) ایجاد می‌کند.
    
    Args:
        schedule: ChecklistSchedule instance
    """
    from datetime import timedelta
    from django.utils import timezone
    
    if not schedule.is_active:
        return
    
    today = timezone.now().date()
    future_date = today + timedelta(days=30)
    
    # دریافت لیست اهداف
    targets = []
    
    if schedule.checklist_type == 'machine':
        if schedule.target_machines:
            from BaseInfo.models import MiningMachine
            targets = MiningMachine.objects.filter(id__in=schedule.target_machines)
        elif schedule.target_machine:
            targets = [schedule.target_machine]
    
    elif schedule.checklist_type == 'location':
        if schedule.target_location_sections:
            from anomalis.models import LocationSection
            targets = LocationSection.objects.filter(id__in=schedule.target_location_sections)
        elif schedule.target_location_section:
            targets = [schedule.target_location_section]
    
    elif schedule.checklist_type == 'contractor_vehicle':
        if schedule.target_contractor_vehicles:
            from contractor_management.models import Vehicle
            targets = Vehicle.objects.filter(id__in=schedule.target_contractor_vehicles)
        elif schedule.target_contractor_vehicle:
            targets = [schedule.target_contractor_vehicle]
    
    if not targets:
        return
    
    # تعیین تاریخ‌هایی که باید instances ایجاد شوند
    dates_to_create = []
    
    if schedule.schedule_type == 'specific_dates':
        # برای specific_dates، تمام تاریخ‌های مشخص شده را ایجاد می‌کنیم
        for date_str in schedule.specific_dates:
            try:
                from datetime import datetime
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                # فقط تاریخ‌های آینده یا امروز را ایجاد می‌کنیم
                if target_date >= today:
                    dates_to_create.append(target_date)
            except (ValueError, TypeError):
                continue
    
    elif schedule.schedule_type == 'monthly_days':
        # برای monthly_days، تاریخ‌های آینده (تا 30 روز) را بررسی می‌کنیم
        current_date = today
        checked_months = set()
        
        while current_date <= future_date:
            # بررسی آیا این روز در لیست monthly_days است
            if current_date.day in schedule.monthly_days:
                dates_to_create.append(current_date)
            
            # رفتن به روز بعد
            current_date += timedelta(days=1)
            
            # جلوگیری از بررسی بیش از حد
            month_key = (current_date.year, current_date.month)
            if month_key in checked_months and current_date.day == 1:
                # اگر این ماه را قبلاً بررسی کرده‌ایم و به روز اول ماه بعد رسیده‌ایم، متوقف می‌شویم
                if len(dates_to_create) >= len(schedule.monthly_days) * 2:  # حداقل 2 ماه
                    break
            checked_months.add(month_key)
            
            if len(dates_to_create) > 100:  # محدودیت برای جلوگیری از حلقه بی‌نهایت
                break
    
    elif schedule.schedule_type == 'weekly':
        # برای weekly، هر دوشنبه (weekday=0) تا 30 روز آینده
        current_date = today
        while current_date <= future_date:
            if current_date.weekday() == 0:  # Monday
                dates_to_create.append(current_date)
            current_date += timedelta(days=1)
            if len(dates_to_create) > 10:  # حداکثر 10 دوشنبه
                break
    
    # ایجاد instances برای هر تاریخ
    # توجه: برای هر schedule یک instance ایجاد می‌شود (نه برای هر target)
    # چون در مدل ScheduledChecklistInstance، schedule و due_date unique_together هستند
    for target_date in dates_to_create:
        instance, created = ScheduledChecklistInstance.objects.get_or_create(
            schedule=schedule,
            due_date=target_date,
            defaults={'status': 'pending'}
        )
        
        # ارسال notification هنگام ایجاد instance جدید
        if created:
            # دریافت کاربران مربوطه (بازرسان ایمنی در شیفت روزکار)
            from .notifications import notify_scheduled_checklist_created
            import logging
            logger = logging.getLogger(__name__)
            
            # دریافت کاربرانی که باید notification دریافت کنند
            # به تمام بازرسان ایمنی که در شیفت روزکار هستند اطلاع می‌دهیم
            try:
                safety_inspectors = get_users_on_shift(target_date, 'روزکار اول')
                if safety_inspectors.exists():
                    inspector_list = list(safety_inspectors)
                    logger.info(f"Sending notification to {len(inspector_list)} safety inspectors for instance {instance.id} (due: {target_date})")
                    notify_scheduled_checklist_created(instance, inspector_list)
                else:
                    logger.warning(f"No safety inspectors found for shift 'روزکار اول' on {target_date}")
            except Exception as e:
                logger.error(f"Error sending notification for scheduled checklist instance {instance.id}: {str(e)}", exc_info=True)


def claim_scheduled_checklist(instance_id: int, user: User):
    """
    ادعای یک چک‌لیست برنامه‌ریزی شده توسط کاربر (اول-به-ادعا)
    
    این تابع با استفاده از select_for_update از race condition جلوگیری می‌کند.
    
    Args:
        instance_id: شناسه ScheduledChecklistInstance
        user: کاربری که می‌خواهد چک‌لیست را تکمیل کند
    
    Returns:
        tuple: (success, instance, error_message)
    """
    try:
        with transaction.atomic():
            # استفاده از select_for_update برای جلوگیری از race condition
            instance = ScheduledChecklistInstance.objects.select_for_update().get(
                pk=instance_id,
                status='pending'
            )
            
            # علامت‌گذاری به عنوان تکمیل شده
            instance.status = 'completed'
            instance.completed_by = user
            instance.completed_at = timezone.now()
            instance.save()
            
            return True, instance, None
    
    except ScheduledChecklistInstance.DoesNotExist:
        return False, None, "چک‌لیست برنامه‌ریزی شده یافت نشد یا قبلاً تکمیل شده است."
    except Exception as e:
        return False, None, f"خطا در ادعای چک‌لیست: {str(e)}"

