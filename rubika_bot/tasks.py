# rubika_bot/tasks.py

import logging
from typing import Any, Dict

from celery import shared_task

from .constants import LOG_CLEANUP_DAYS
from .models import WebhookLog
from .services import RubPyIntegrationService

logger = logging.getLogger(__name__)


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
            message_lines = [
                '🔔 درخواست جایگزینی مرخصی',
                '',
                f'👤 درخواست‌دهنده: {requester_name}',
                f'📌 نوع مرخصی: {leave_type_display}',
                f'📅 تاریخ: {leave_request.shift_date}',
                f'🕐 شیفت: {shift_type_display}',
            ]
        else:  # manager
            message_lines = [
                '🔔 درخواست تایید مرخصی',
                '',
                f'👤 درخواست‌دهنده: {requester_name}',
                f'📌 نوع مرخصی: {leave_type_display}',
                f'📅 تاریخ: {leave_request.shift_date}',
                f'🕐 شیفت: {shift_type_display}',
            ]
            
            # اگر جایگزین دارد، نمایش بده
            if leave_request.replacement_person:
                replacement_name = leave_request.replacement_person.get_full_name() or leave_request.replacement_person.username
                message_lines.append(f'👥 جایگزین: {replacement_name}')
        
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
        
        logger.info(
            f"Task 'send_leave_approval_request' successfully sent to {chat_id} for leave {leave_request_id}"
        )
        
    except Exception as exc:
        logger.error(
            f"Error in 'send_leave_approval_request' for chat {chat_id}, leave {leave_request_id}: {exc}",
            exc_info=True,
        )
        raise self.retry(exc=exc)
