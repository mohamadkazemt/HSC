"""
Celery tasks for checklist_app
"""
from celery import shared_task
from django.utils import timezone
from datetime import date, timedelta
from .services import create_scheduled_instances_for_date, get_users_on_shift
from .models import ScheduledChecklistInstance
from .notifications import notify_pending_scheduled_checklists, notify_scheduled_checklist_due_soon
import logging

logger = logging.getLogger(__name__)


@shared_task
def create_scheduled_checklist_instances():
    """
    Celery task to create scheduled checklist instances for today and next 30 days.
    
    This task should be scheduled to run daily (e.g., at 00:00) using Celery Beat.
    """
    try:
        today = timezone.now().date()
        # ایجاد instances برای امروز و 30 روز آینده
        for i in range(31):  # امروز + 30 روز آینده
            target_date = today + timedelta(days=i)
            create_scheduled_instances_for_date(target_date)
        
        logger.info(f"Successfully created scheduled checklist instances for dates from {today} to {today + timedelta(days=30)}")
        return {'status': 'success', 'message': f'Created instances for 31 days starting from {today}'}
    
    except Exception as e:
        logger.error(f"Error creating scheduled checklist instances: {str(e)}", exc_info=True)
        return {'status': 'error', 'message': str(e)}


@shared_task
def send_scheduled_checklist_reminders():
    """
    ارسال یادآوری برای چک‌لیست‌های برنامه‌ریزی شده
    
    این task باید روزانه اجرا شود (مثلاً ساعت 08:00) تا:
    1. به کاربرانی که چک‌لیست‌های در انتظار دارند اطلاع دهد
    2. یک روز قبل از موعد، یادآوری ارسال کند
    """
    try:
        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)
        
        # 1. اطلاع‌رسانی به کاربرانی که چک‌لیست‌های در انتظار برای امروز دارند
        pending_today = ScheduledChecklistInstance.objects.filter(
            status='pending',
            due_date=today,
            schedule__is_active=True
        ).select_related('schedule')
        
        # دریافت کاربران مربوطه و ارسال notification
        from accounts.models import UserProfile
        from django.contrib.auth.models import User
        
        notified_users = set()
        for instance in pending_today:
            try:
                # دریافت بازرسان ایمنی در شیفت روزکار
                safety_inspectors = get_users_on_shift(today, 'روزکار اول')
                for user in safety_inspectors:
                    if user.id not in notified_users:
                        # دریافت تمام چک‌لیست‌های در انتظار این کاربر
                        from .services import get_pending_scheduled_checklists
                        user_pending = list(get_pending_scheduled_checklists(user, today))
                        if user_pending:
                            notify_pending_scheduled_checklists(user, user_pending)
                            notified_users.add(user.id)
            except Exception as e:
                logger.warning(f"Error sending reminder for instance {instance.id}: {str(e)}")
        
        # 2. یادآوری یک روز قبل از موعد
        pending_tomorrow = ScheduledChecklistInstance.objects.filter(
            status='pending',
            due_date=tomorrow,
            schedule__is_active=True
        ).select_related('schedule')
        
        for instance in pending_tomorrow:
            try:
                safety_inspectors = get_users_on_shift(tomorrow, 'روزکار اول')
                if safety_inspectors.exists():
                    notify_scheduled_checklist_due_soon(instance, list(safety_inspectors), days_before=1)
            except Exception as e:
                logger.warning(f"Error sending due soon reminder for instance {instance.id}: {str(e)}")
        
        logger.info(f"Successfully sent scheduled checklist reminders for {today}")
        return {'status': 'success', 'message': f'Sent reminders for {today}'}
    
    except Exception as e:
        logger.error(f"Error sending scheduled checklist reminders: {str(e)}", exc_info=True)
        return {'status': 'error', 'message': str(e)}

