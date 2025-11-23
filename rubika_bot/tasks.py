# rubika_bot/tasks.py

import logging
from datetime import datetime
from typing import Any, Dict

import jdatetime
from celery import shared_task

from .constants import LOG_CLEANUP_DAYS
from .models import WebhookLog
from .services import RubPyIntegrationService

logger = logging.getLogger(__name__)


def _format_jalali_date(date_value):
    """Format Gregorian date into a Jalali YYYY/MM/DD string."""
    if not date_value:
        return 'نامشخص'
    if isinstance(date_value, datetime):
        date_value = date_value.date()
    try:
        jalali_date = jdatetime.date.fromgregorian(date=date_value)
        return f'{jalali_date.year:04d}/{jalali_date.month:02d}/{jalali_date.day:02d}'
    except Exception:
        return str(date_value)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_rubika_message(self, chat_id: str, text: str) -> None:
    """
    Sends a text message using the RubPy service. This task is designed to be
    called from synchronous parts of the app (e.g., signals, admin views).
    """
    logger.info(f"📨 Task 'send_rubika_message' started for chat_id: {chat_id}")
    logger.info(f"   Message length: {len(text)} characters")
    
    try:
        # Get the singleton instance of the service within the task
        logger.info("   Getting RubPyIntegrationService instance...")
        service = RubPyIntegrationService.get_instance()
        logger.info("   ✅ Service instance obtained")

        # The service method handles the sync/async wrapping internally
        logger.info(f"   Sending message to {chat_id}...")
        service.send_text_message(chat_id, text)

        logger.info(
            "✅ Task 'send_rubika_message' successfully sent message to %s.",
            chat_id,
        )

    except Exception as exc:
        logger.error(
            "❌ Error in 'send_rubika_message' task for %s: %s",
            chat_id,
            exc,
            exc_info=True,
        )
        # Retry the task if an exception occurs
        raise self.retry(exc=exc)


@shared_task
def cleanup_webhook_logs() -> int:
    """Periodically cleans up old webhook logs."""
    deleted, _ = WebhookLog.cleanup_old_logs(days=LOG_CLEANUP_DAYS)
    logger.info("Cleaned up %s old webhook logs.", deleted)
    return deleted


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def process_webhook_task(self, payload: Dict[str, Any]) -> None:
    """
    Processes an incoming webhook payload in the background.
    """
    logger.info(
        "Task 'process_webhook_task' started for payload: %s",
        payload.get("update", {}).get("type"),
    )
    try:
        service = RubPyIntegrationService.get_instance()
        service.handle_webhook_payload(payload)
        logger.info("Task 'process_webhook_task' succeeded.")
    except Exception as exc:
        logger.error(
            "Error in 'process_webhook_task': %s",
            exc,
            exc_info=True,
        )
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_leave_approval_request(self, chat_id: str, leave_request_id: int, approval_type: str = 'replacement') -> None:
    """
    ارسال درخواست تایید مرخصی با دکمه‌های تایید/رد به ربات روبیکا
    
    Parameters:
    - chat_id: شناسه چت کاربر در روبیکا
    - leave_request_id: شناسه درخواست مرخصی
    - approval_type: نوع تایید ('replacement' یا 'manager')
    """
    try:
        from leave_reports.models import ShiftReport
        from rubpy.bot.models import Keypad, KeypadRow, Button
        from rubpy.bot.enums import ButtonTypeEnum
        
        # دریافت درخواست مرخصی
        try:
            leave_request = ShiftReport.objects.select_related(
                'user', 'user__userprofile', 'replacement_person'
            ).get(id=leave_request_id)
        except ShiftReport.DoesNotExist:
            logger.error(f"Leave request {leave_request_id} not found")
            return
        
        # ساختن متن پیام
        leave_type_display = leave_request.get_leave_type_display()
        requester_name = leave_request.user.get_full_name() or leave_request.user.username
        shift_type_display = leave_request.get_shift_type_display()
        
        message_lines = []
        
        if approval_type == 'replacement':
            # ساختن اطلاعات درخواست‌دهنده با کد پرسنلی
            requester_info = f'👤 درخواست‌دهنده: {requester_name}'
            requester_profile = getattr(leave_request.user, 'userprofile', None)
            if requester_profile and requester_profile.personnel_code:
                requester_info += f' (کد پرسنلی: {requester_profile.personnel_code})'
            
            message_lines = [
                '🔔 درخواست جایگزینی مرخصی',
                '',
                requester_info,
                f'📌 نوع مرخصی: {leave_type_display}',
                f'📅 تاریخ: {_format_jalali_date(leave_request.shift_date)}',
                f'🕐 شیفت: {shift_type_display}',
            ]
        else:  # manager
            # ساختن اطلاعات درخواست‌دهنده با کد پرسنلی
            requester_info = f'👤 درخواست‌دهنده: {requester_name}'
            requester_profile = getattr(leave_request.user, 'userprofile', None)
            if requester_profile and requester_profile.personnel_code:
                requester_info += f' (کد پرسنلی: {requester_profile.personnel_code})'
            
            message_lines = [
                '🔔 درخواست تایید مرخصی',
                '',
                requester_info,
                f'📌 نوع مرخصی: {leave_type_display}',
                f'📅 تاریخ: {_format_jalali_date(leave_request.shift_date)}',
                f'🕐 شیفت: {shift_type_display}',
            ]
            
            # اگر جایگزین دارد، نمایش بده
            if leave_request.replacement_person:
                replacement_name = leave_request.replacement_person.get_full_name() or leave_request.replacement_person.username
                replacement_info = f'👥 جایگزین: {replacement_name}'
                
                # اضافه کردن کد پرسنلی جایگزین
                replacement_profile = getattr(leave_request.replacement_person, 'userprofile', None)
                if replacement_profile and replacement_profile.personnel_code:
                    replacement_info += f' (کد پرسنلی: {replacement_profile.personnel_code})'
                
                message_lines.append(replacement_info)
        
        # اضافه کردن توضیحات اگر وجود داشت
        if leave_request.description:
            message_lines.extend([
                '',
                f'📝 توضیحات: {leave_request.description}'
            ])
        
        # اضافه کردن ساعات برای مرخصی ساعتی
        if leave_request.leave_type == 'hourly' and leave_request.start_time and leave_request.end_time:
            message_lines.append(f'⏰ ساعات: {leave_request.start_time.strftime("%H:%M")} تا {leave_request.end_time.strftime("%H:%M")}')
        
        message_lines.extend([
            '',
            '❓ لطفاً تصمیم خود را اعلام کنید:',
        ])
        
        message = '\n'.join(message_lines)
        
        # ساختن دکمه‌های تایید و رد
        approve_button_id = f'approve_leave_{approval_type}_{leave_request_id}'
        reject_button_id = f'reject_leave_{approval_type}_{leave_request_id}'
        
        keyboard = Keypad(rows=[
            KeypadRow(buttons=[
                Button(
                    id=approve_button_id,
                    type=ButtonTypeEnum.SIMPLE,
                    button_text='✅ تایید'
                ),
                Button(
                    id=reject_button_id,
                    type=ButtonTypeEnum.SIMPLE,
                    button_text='❌ رد'
                )
            ])
        ])
        
        # ارسال پیام
        service = RubPyIntegrationService.get_instance()
        service._run_sync(
            service.engine._send_text_message(chat_id, message, keyboard)
        )
        
        # ثبت لاگ ارسال
        from rubika_bot.models import WebhookLog
        WebhookLog.log_outgoing(
            title=f'ارسال درخواست تایید {approval_type}',
            message=f'پیام درخواست تایید برای مرخصی #{leave_request_id} به {chat_id} ارسال شد',
            data={
                'leave_id': leave_request_id,
                'approval_type': approval_type,
                'chat_id': chat_id,
                'requester': requester_name
            }
        )
        
        logger.info(
            f"Task 'send_leave_approval_request' successfully sent to {chat_id} for leave {leave_request_id}"
        )
        
    except Exception as exc:
        logger.error(
            f"Error in 'send_leave_approval_request' for chat {chat_id}, leave {leave_request_id}: {exc}",
            exc_info=True,
        )
        raise self.retry(exc=exc)
