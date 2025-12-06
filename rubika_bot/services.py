# rubika_bot/services.py

from __future__ import annotations

import asyncio
import logging
import threading
from concurrent.futures import Future
from typing import Any, Awaitable, Dict, Iterable, List, Optional, Sequence, Tuple, Union

from asgiref.sync import sync_to_async, async_to_sync
from django.conf import settings
from django.db import close_old_connections
from django.utils import timezone
from rubpy.bot.enums import ButtonTypeEnum
from rubpy.bot.models import InlineMessage, Keypad, KeypadRow, Message, Update
from rubpy.bot.bot import BotClient
from rubpy.exceptions import APIException

try:
    from aiohttp_socks import ProxyConnector
except ImportError:  # pragma: no cover - only when extra dependency missing
    ProxyConnector = None  # type: ignore[assignment]

from .constants import BOT_REQUEST_TIMEOUT
from .models import RubikaBotSettings, RubikaConnectionCode, RubikaUser, WebhookLog

logger = logging.getLogger(__name__)

# Helper functions remain the same
def _safe_str(value: Any) -> str:
    return "" if value is None else str(value)


def normalize_digits(text: str) -> str:
    """
    تبدیل اعداد فارسی (۰-۹) و عربی (٠-٩) به انگلیسی (0-9)
    
    Args:
        text: متن ورودی که ممکن است شامل اعداد فارسی یا عربی باشد
    
    Returns:
        متن با اعداد انگلیسی
    
    Examples:
        >>> normalize_digits("۱۴۰۳/۰۹/۱۵")
        "1403/09/15"
        >>> normalize_digits("۰۹۱۲۳۴۵۶۷۸۹")
        "09123456789"
        >>> normalize_digits("٠٩١٢٣٤٥٦٧٨٩")
        "09123456789"
    """
    if not text:
        return text
    
    # اعداد فارسی
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    # اعداد عربی
    arabic_digits = '٠١٢٣٤٥٦٧٨٩'
    # اعداد انگلیسی
    english_digits = '0123456789'
    
    # ساخت جدول ترجمه
    translation_table = str.maketrans(
        persian_digits + arabic_digits,
        english_digits + english_digits
    )
    
    return text.translate(translation_table)


def _extract_button_id(message: Optional[Message]) -> Optional[str]:
    # ... (این تابع بدون تغییر باقی می‌ماند) ...
    if not message or not message.aux_data:
        return None
    aux = message.aux_data
    if isinstance(aux, dict):
        button_id = aux.get("button_id")
        if not button_id:
            for value in aux.values():
                if isinstance(value, dict) and value.get("button_id"):
                    return str(value["button_id"])
        return _safe_str(button_id) or None
    try:
        return _safe_str(getattr(aux, 'button_id', None))
    except AttributeError:
        return None


class RubikaBotEngine:
    def __init__(self, client: BotClient):
        self.client = client

    # --- ASYNC REFACTORED METHODS ---

    async def handle_update(self, update: Update) -> None:
        message = update.new_message or update.updated_message
        if not message:
            return
        chat_id = _safe_str(update.chat_id)
        raw_payload = getattr(update, "_raw_payload", {})
        rubika_user = await self._ensure_profile(chat_id, message, raw_payload)
        button_id = _extract_button_id(message)
        text = (message.text or "").strip()

        if button_id:
            await self._handle_button(chat_id, button_id, rubika_user)
        elif text.startswith("/"):
            await self._handle_command(chat_id, text, rubika_user)
        elif text:
            await self._handle_plain_text(chat_id, text, rubika_user)

    async def handle_inline(self, inline_update: InlineMessage) -> None:
        chat_id = _safe_str(inline_update.chat_id)
        button_id = None
        aux = inline_update.aux_data
        if isinstance(aux, dict):
            button_id = aux.get("button_id")
        elif hasattr(aux, "button_id"):
            button_id = aux.button_id
        if button_id:
            user = await sync_to_async(RubikaUser.get_or_create_by_chat, thread_sensitive=True)(chat_id)
            await sync_to_async(user.touch_seen, thread_sensitive=True)()
            await self._handle_button(chat_id, str(button_id), user)

    async def _ensure_profile(self, chat_id: str, message: Message, raw_payload: Dict[str, Any]) -> RubikaUser:
        defaults: Dict[str, Any] = {'metadata': {'raw': raw_payload}}
        first_name, last_name = self._extract_names(raw_payload, message)
        if first_name: defaults['first_name'] = first_name
        if last_name: defaults['last_name'] = last_name

        rubika_user, created = await sync_to_async(RubikaUser.objects.get_or_create, thread_sensitive=True)(chat_id=chat_id, defaults=defaults)
        
        # Optimized: Update last_seen and other fields in a single query if needed
        if not created:
            attrs_to_update: Dict[str, Any] = {'last_seen': timezone.now()}
            if first_name and rubika_user.first_name != first_name: attrs_to_update['first_name'] = first_name
            if last_name and rubika_user.last_name != last_name: attrs_to_update['last_name'] = last_name
            if len(attrs_to_update) > 1:  # More than just last_seen
                await sync_to_async(RubikaUser.objects.filter(pk=rubika_user.pk).update, thread_sensitive=True)(**attrs_to_update)
                for key, value in attrs_to_update.items():
                    setattr(rubika_user, key, value)
            else:
                # Only update last_seen
                await sync_to_async(rubika_user.touch_seen, thread_sensitive=True)()
        else:
            # New user, last_seen is already set in defaults or will be set on first touch_seen
            await sync_to_async(rubika_user.touch_seen, thread_sensitive=True)()
        return rubika_user

    def _extract_names(self, raw_payload: Dict[str, Any], message: Message) -> Tuple[Optional[str], Optional[str]]:
        # This method does not touch the DB, so it remains synchronous.
        # ... (کد این تابع بدون تغییر باقی می‌ماند) ...
        user_info = {}
        if isinstance(raw_payload, dict):
            user_info = (raw_payload.get('message', {}).get('user') or raw_payload.get('user') or {})
        first_name = user_info.get('first_name')
        last_name = user_info.get('last_name')
        if not first_name and message:
            first_name = getattr(message, 'first_name', None)
            last_name = getattr(message, 'last_name', None)
        return first_name, last_name

    async def _handle_button(self, chat_id: str, button_id: str, user: RubikaUser) -> None:
        mapping = {
            'start': self._send_welcome, 'help': self._send_help, 'connect': self._handle_connect_button,
            'disconnect': self._disconnect_user, 'account': self._send_account_status,
            'payslip': self._handle_payslip_request,
            'leave_request': self._start_leave_request,
            'cancel_leave': self._cancel_leave_request,
            'cancel_rejection': self._cancel_rejection,
            'sms_connect': self._start_sms_connection,
            'cancel_sms_connect': self._cancel_sms_connection,
            'paste_connection_code': self._prompt_paste_connection_code,
        }
        handler = mapping.get(button_id.lower())
        if handler:
            await handler(chat_id, user)
        else:
            # Check if it's a payslip selection button (format: payslip_YYYY_MM)
            if button_id.startswith('payslip_'):
                await self._send_payslip_file(chat_id, user, button_id)
            # Check if it's a leave type selection button
            elif button_id.startswith('leavetype_'):
                await self._handle_leave_type_selection(chat_id, user, button_id)
            # Check if it's a shift type selection button
            elif button_id.startswith('shifttype_'):
                await self._handle_shift_type_selection(chat_id, user, button_id)
            # Check if it's a replacement selection button
            elif button_id.startswith('replacement_'):
                await self._handle_replacement_selection(chat_id, user, button_id)
            # Check if it's a replacement confirmation button
            elif button_id in ['confirm_replacement', 'reject_replacement']:
                await self._handle_replacement_selection(chat_id, user, button_id)
            # Check if it's a final confirmation button
            elif button_id in ['confirm_leave', 'edit_leave']:
                await self._handle_leave_confirmation(chat_id, user, button_id)
            # Check if it's a leave approval/rejection button (format: approve_leave_replacement_123 or reject_leave_manager_456)
            elif button_id.startswith('approve_leave_') or button_id.startswith('reject_leave_'):
                await self._handle_leave_approval_action(chat_id, user, button_id)
            else:
                logger.debug("Unknown button id %s for chat %s", button_id, chat_id)

    async def _handle_command(self, chat_id: str, text: str, user: RubikaUser) -> None:
        parts = text.split()
        command, args = parts[0].lstrip('/').lower(), parts[1:]

        if command in {'help', 'راهنما'}: await self._send_help(chat_id, user)
        elif command in {'account', 'status'}: await self._send_account_status(chat_id, user)
        elif command == 'disconnect': await self._disconnect_user(chat_id, user)
        elif command == 'connect': await self._process_connection_code(chat_id, user, args)
        elif command == 'start':
            await self._process_connection_code(chat_id, user, args) if args else await self._send_welcome(chat_id, user)
        else:
            await self._handle_plain_text(chat_id, text, user)

    async def _handle_plain_text(self, chat_id: str, text: str, user: RubikaUser) -> None:
        # Optimized: Fetch both states in a single query batch
        @sync_to_async(thread_sensitive=True)
        def get_states():
            from rubika_bot.models import ConnectionRequestState, LeaveRequestState
            connection_state = None
            leave_state = None
            try:
                connection_state = ConnectionRequestState.objects.get(rubika_user=user)
            except ConnectionRequestState.DoesNotExist:
                pass
            try:
                leave_state = LeaveRequestState.objects.get(rubika_user=user)
            except LeaveRequestState.DoesNotExist:
                pass
            return connection_state, leave_state
        
        connection_state, leave_state = await get_states()
        
        # If in SMS connection flow, handle accordingly
        if connection_state and connection_state.step != 'idle':
            await self._handle_sms_connection_input(chat_id, user, text, connection_state)
            return
        
        # If in leave request flow, handle accordingly
        if leave_state and leave_state.step != 'idle':
            # بررسی اینکه آیا در مرحله وارد کردن دلیل رد است
            if leave_state.step == 'rejection_reason':
                await self._process_rejection_reason(chat_id, user, text, leave_state)
                return
            
            await self._handle_leave_request_input(chat_id, user, text, leave_state)
            return
        
        # Normal text handling
        lowered = text.strip().lower()
        display_name = self._display_name(user)
        
        # پاسخ به سلام و احوال‌پرسی
        if lowered.startswith('سلام') or lowered in {'hi', 'hello', 'hey', 'درود', 'salam', 'سلام علیکم'}:
            if user.user:
                reply = f'👋 سلام {display_name} عزیز!\n\n✨ چطور می‌تونم کمکت کنم؟'
            else:
                reply = f'👋 سلام {display_name} عزیز!\n\n⚠️ لطفاً ابتدا به حساب کاربری خود متصل شوید.\n\n💡 از دکمه‌های زیر استفاده کنید:'
        
        # پاسخ به سپاسگزاری
        elif lowered in {'ممنون', 'متشکرم', 'مرسی', 'thanks', 'thank you', 'تشکر'}:
            reply = f'🌟 خواهش می‌کنم {display_name}!\n\nخوشحالیم که تونستیم کمکتون کنیم. 😊'
        
        # پاسخ به خداحافظی
        elif lowered in {'خداحافظ', 'بای', 'bye', 'خدافظ', 'فعلا'}:
            reply = f'👋 خداحافظ {display_name}!\n\nموفق باشید. 🌟'
        
        # سایر پیام‌ها
        else:
            if user.user:
                reply = f'💬 پیام شما دریافت شد:\n"{text}"\n\n💡 از دکمه‌های منو برای دسترسی سریع استفاده کنید.'
            else:
                reply = f'💬 پیام شما دریافت شد:\n"{text}"\n\n⚠️ برای استفاده از امکانات ربات، لطفاً ابتدا وصل شوید.'
        
        buttons = self._build_command_keyboard(connected=bool(user.user))
        await self._send_text_message(chat_id, reply, buttons)

    async def _send_welcome(self, chat_id: str, user: RubikaUser) -> None:
        """ارسال پیام خوش‌آمدگویی با اطلاعات کامل کاربر"""
        display_name = self._display_name(user)
        
        if user.user:
            # دریافت اطلاعات کامل کاربر
            @sync_to_async(thread_sensitive=True)
            def get_user_info():
                from accounts.models import UserProfile
                try:
                    profile = UserProfile.objects.select_related('position', 'section').get(user=user.user)
                    
                    # نام کامل
                    full_name = user.user.get_full_name()
                    if not full_name:
                        full_name = user.user.username
                    
                    # کد پرسنلی
                    personnel_code = profile.personnel_code or 'نامشخص'
                    
                    # سمت
                    position = profile.position.name if profile.position else None
                    
                    # بخش
                    section = profile.section.name if profile.section else None
                    
                    return {
                        'full_name': full_name,
                        'personnel_code': personnel_code,
                        'position': position,
                        'section': section,
                    }
                except UserProfile.DoesNotExist:
                    return {
                        'full_name': user.user.get_full_name() or user.user.username,
                        'personnel_code': None,
                        'position': None,
                        'section': None,
                    }
            
            user_info = await get_user_info()
            
            # ساخت پیام خوش‌آمدگویی با اطلاعات کامل
            message_lines = [
                f'👋 سلام {user_info["full_name"]} عزیز!',
            ]
            
            # اضافه کردن کد پرسنلی اگر موجود باشد
            if user_info['personnel_code']:
                message_lines.append(f'🆔 کد پرسنلی: {user_info["personnel_code"]}')
            
            # اضافه کردن سمت و بخش اگر موجود باشد
            if user_info['position'] or user_info['section']:
                info_parts = []
                if user_info['position']:
                    info_parts.append(f'💼 {user_info["position"]}')
                if user_info['section']:
                    info_parts.append(f'🏢 {user_info["section"]}')
                message_lines.append(' | '.join(info_parts))
            
            message_lines.extend([
                '',
                '✅ شما به حساب خود متصل هستید.',
                '',
                '🎯 از منوی زیر می‌توانید:',
                '   💰 فیش حقوقی دریافت کنید',
                '   🏖️ درخواست مرخصی ثبت کنید',
                '   👤 اطلاعات حساب را مشاهده کنید',
                '',
                '👇 دکمه مورد نظر را انتخاب کنید:'
            ])
        else:
            # پیام خوش‌آمدگویی برای کاربر غیر متصل
            message_lines = [
                f'👋 سلام {display_name} عزیز!',
                '',
                '🤖 به ربات خوش آمدید!',
                '',
                '⚠️ برای استفاده از امکانات ربات، ابتدا باید به حساب کاربری خود متصل شوید.',
                '',
                '🔗 دو روش برای اتصال:',
                '   1️⃣ اتصال با کد (از پنل وب)',
                '   2️⃣ اتصال با پیامک (احراز هویت)',
                '',
                '👇 یکی از روش‌های زیر را انتخاب کنید:'
            ]
        
        buttons = self._build_command_keyboard(connected=bool(user.user))
        await self._send_text_message(chat_id, '\n'.join(message_lines), buttons)

    async def _send_help(self, chat_id: str, user: RubikaUser) -> None:
        message = (
            '📖 راهنمای ربات:\n\n'
            '🔹 `/start` - بازگشت به منوی اصلی\n'
            '🔹 `/connect [کد]` - اتصال با کد\n'
            '🔹 `/account` - مشاهده وضعیت حساب\n'
            '🔹 `/disconnect` - قطع اتصال\n'
            '🔹 `/help` - نمایش راهنما\n\n'
            '💡 می‌توانید از دکمه‌های زیر نیز استفاده کنید:'
        )
        buttons = self._build_command_keyboard(connected=bool(user.user))
        await self._send_text_message(chat_id, message, buttons)

    async def _handle_connect_button(self, chat_id: str, user: RubikaUser) -> None:
        message = (
            '🔗 اتصال به حساب کاربری\n\n'
            'برای اتصال، کد را از پنل وب دریافت کنید و دستور زیر را ارسال کنید:\n'
            '`/connect [کد]`\n\n'
            'مثال:\n'
            '`/connect abc123def456`'
        )
        keyboard = Keypad(rows=[
            KeypadRow(buttons=[self._button('start', '🏠 بازگشت به منوی اصلی')])
        ])
        await self._send_text_message(chat_id, message, keyboard)

    async def _send_account_status(self, chat_id: str, user: RubikaUser) -> None:
        """نمایش وضعیت حساب کاربری با جزئیات کامل"""
        display_name = self._display_name(user)
        
        if user.user:
            # دریافت اطلاعات پروفایل کاربر
            @sync_to_async(thread_sensitive=True)
            def get_profile_info():
                from accounts.models import UserProfile
                try:
                    profile = UserProfile.objects.select_related('position', 'section').get(user=user.user)
                    
                    # نام کامل
                    full_name = user.user.get_full_name()
                    if not full_name:
                        full_name = user.user.username
                    
                    # کد پرسنلی
                    personnel_code = profile.personnel_code or 'نامشخص'
                    
                    # سمت
                    position = profile.position.name if profile.position else 'نامشخص'
                    
                    # بخش
                    section = profile.section.name if profile.section else 'نامشخص'
                    
                    # عکس پروفایل
                    image_path = None
                    if profile.image:
                        try:
                            image_path = profile.image.path
                        except Exception:
                            image_path = None
                    
                    return {
                        'full_name': full_name,
                        'personnel_code': personnel_code,
                        'position': position,
                        'section': section,
                        'image_path': image_path,
                        'username': user.user.username
                    }
                except UserProfile.DoesNotExist:
                    return {
                        'full_name': user.user.get_full_name() or user.user.username,
                        'personnel_code': 'نامشخص',
                        'position': 'نامشخص',
                        'section': 'نامشخص',
                        'image_path': None,
                        'username': user.user.username
                    }
            
            profile_info = await get_profile_info()
            
            # ساخت پیام
            message_lines = [
                '👤 اطلاعات حساب کاربری',
                '',
                f'✅ وضعیت: متصل',
                f'👤 نام: {profile_info["full_name"]} ({profile_info["personnel_code"]})',
                f'💼 سمت: {profile_info["position"]}',
                f'🏢 بخش: {profile_info["section"]}',
                f'🆔 نام کاربری: {profile_info["username"]}',
            ]
            
            message = '\n'.join(message_lines)
            
            # ارسال عکس پروفایل اگر موجود باشد
            if profile_info['image_path']:
                try:
                    # ارسال عکس با کپشن
                    def send_profile_image():
                        from rubika_bot.services import RubPyIntegrationService
                        service = RubPyIntegrationService.get_instance()
                        return service._run_sync(
                            service.client.send_file(
                                chat_id=chat_id,
                                file=profile_info['image_path'],
                                text=message,
                                type='Image'
                            )
                        )
                    
                    await sync_to_async(send_profile_image, thread_sensitive=True)()
                    
                    # ارسال دکمه‌ها به صورت جداگانه
                    buttons = self._build_command_keyboard(connected=True)
                    await self._send_text_message(chat_id, '👇 از منوی زیر استفاده کنید:', buttons)
                    
                    logger.info(f"Sent profile image to {chat_id}")
                except Exception as e:
                    logger.error(f"Error sending profile image: {e}", exc_info=True)
                    # اگر ارسال عکس با خطا مواجه شد، فقط متن را ارسال کن
                    buttons = self._build_command_keyboard(connected=True)
                    await self._send_text_message(chat_id, message, buttons)
            else:
                # اگر عکس نداشت، فقط متن را با دکمه‌ها ارسال کن
                buttons = self._build_command_keyboard(connected=True)
                await self._send_text_message(chat_id, message, buttons)
        else:
            message = f'📊 وضعیت حساب:\n\n❌ متصل نشده\n👤 نام: {display_name}\n\n💡 برای اتصال از دکمه‌های زیر استفاده کنید:'
            buttons = self._build_command_keyboard(connected=False)
            await self._send_text_message(chat_id, message, buttons)

    async def _disconnect_user(self, chat_id: str, user: RubikaUser) -> None:
        if user.user:
            username = user.user.username
            user.user = None
            await sync_to_async(user.save, thread_sensitive=True)(update_fields=['user'])
            message = f'✅ حساب کاربری "{username}" با موفقیت قطع شد.\n\n💡 برای اتصال مجدد می‌توانید از دکمه‌های زیر استفاده کنید:'
        else:
            message = '⚠️ شما به هیچ حساب کاربری متصل نیستید.'
        
        buttons = self._build_command_keyboard(connected=False)
        await self._send_text_message(chat_id, message, buttons)

    async def _handle_payslip_request(self, chat_id: str, user: RubikaUser) -> None:
        """نمایش لیست فیش‌های حقوقی موجود برای کاربر"""
        # Import در ابتدای تابع
        from rubpy.bot.models import Keypad, KeypadRow
        
        if not user.user:
            message = '⚠️ برای دریافت فیش حقوقی، ابتدا باید به حساب کاربری خود متصل شوید.\n\n🔗 از دکمه‌های زیر برای اتصال استفاده کنید:'
            buttons = self._build_command_keyboard(connected=False)
            await self._send_text_message(chat_id, message, buttons)
            return
        
        # Get user profile and payslips (optimized with select_related)
        @sync_to_async(thread_sensitive=True)
        def get_payslips():
            from accounts.models import UserProfile, Payslip
            try:
                profile = UserProfile.objects.select_related('position', 'section').get(user=user.user)
                payslips = list(Payslip.objects.filter(user_profile=profile).order_by('-year', '-month')[:12])
                return profile, payslips
            except UserProfile.DoesNotExist:
                return None, []
        
        profile, payslips = await get_payslips()
        
        if not profile:
            message = '⚠️ پروفایل کاربری شما یافت نشد.\n\nلطفاً با پشتیبانی تماس بگیرید.'
            keyboard = Keypad(rows=[
                KeypadRow(buttons=[self._button('start', '🏠 بازگشت به منوی اصلی')])
            ])
            await self._send_text_message(chat_id, message, keyboard)
            return
        
        if not payslips:
            message = '📭 هیچ فیش حقوقی برای شما ثبت نشده است.'
            keyboard = Keypad(rows=[
                KeypadRow(buttons=[self._button('start', '🏠 بازگشت به منوی اصلی')])
            ])
            await self._send_text_message(chat_id, message, keyboard)
            return
        
        # Build keyboard with available payslips
        message_lines = [
            '💰 فیش‌های حقوقی موجود:',
            '',
            '👇 یکی از ماه‌های زیر را انتخاب کنید:'
        ]
        
        # Create buttons for each payslip (max 2 per row)
        rows = []
        current_row = []
        
        # Persian month names
        persian_months = {
            1: 'فروردین', 2: 'اردیبهشت', 3: 'خرداد', 4: 'تیر',
            5: 'مرداد', 6: 'شهریور', 7: 'مهر', 8: 'آبان',
            9: 'آذر', 10: 'دی', 11: 'بهمن', 12: 'اسفند'
        }
        
        for payslip in payslips:
            month_name = persian_months.get(payslip.month, str(payslip.month))
            button_id = f'payslip_{payslip.year}_{payslip.month}'
            button_label = f'{month_name} {payslip.year}'
            
            current_row.append((button_id, button_label))
            
            if len(current_row) == 2:
                rows.append(current_row)
                current_row = []
        
        # Add remaining button if any
        if current_row:
            rows.append(current_row)
        
        # Add back button
        rows.append([('start', '🏠 بازگشت به منوی اصلی')])
        
        keypad_rows = [KeypadRow(buttons=[self._button(button_id, label) for button_id, label in row]) for row in rows]
        keyboard = Keypad(rows=keypad_rows)
        
        await self._send_text_message(chat_id, '\n'.join(message_lines), keyboard)

    async def _send_payslip_file(self, chat_id: str, user: RubikaUser, button_id: str) -> None:
        """ارسال فایل فیش حقوقی به کاربر"""
        if not user.user:
            message = '⚠️ برای دریافت فیش حقوقی، ابتدا باید به حساب کاربری خود متصل شوید.'
            await self._send_text_message(chat_id, message)
            return
        
        # Parse button_id to extract year and month (format: payslip_YYYY_MM)
        try:
            parts = button_id.split('_')
            year = int(parts[1])
            month = int(parts[2])
        except (IndexError, ValueError):
            message = '❌ خطا در شناسایی فیش حقوقی.'
            await self._send_text_message(chat_id, message)
            return
        
        # Get payslip from database (optimized with select_related)
        @sync_to_async(thread_sensitive=True)
        def get_payslip():
            from accounts.models import UserProfile, Payslip
            try:
                profile = UserProfile.objects.select_related('position', 'section').get(user=user.user)
                payslip = Payslip.objects.select_related('user_profile').get(user_profile=profile, year=year, month=month)
                return payslip
            except (UserProfile.DoesNotExist, Payslip.DoesNotExist):
                return None
        
        payslip = await get_payslip()
        
        if not payslip:
            message = '❌ فیش حقوقی مورد نظر یافت نشد.'
            keyboard = Keypad(rows=[
                KeypadRow(buttons=[self._button('payslip', '🔙 بازگشت به لیست'), self._button('start', '🏠 منوی اصلی')])
            ])
            await self._send_text_message(chat_id, message, keyboard)
            return
        
        if not payslip.file:
            message = '❌ فایل فیش حقوقی موجود نیست.'
            keyboard = Keypad(rows=[
                KeypadRow(buttons=[self._button('payslip', '🔙 بازگشت به لیست'), self._button('start', '🏠 منوی اصلی')])
            ])
            await self._send_text_message(chat_id, message, keyboard)
            return
        
        # Send file to user
        try:
            # Get file path
            @sync_to_async(thread_sensitive=True)
            def get_file_path():
                try:
                    return payslip.file.path
                except Exception as e:
                    logger.error(f"Error getting payslip file path: {e}")
                    return None
            
            file_path = await get_file_path()
            
            if not file_path:
                message = '❌ خطا در دسترسی به فایل فیش حقوقی.'
                keyboard = Keypad(rows=[
                    KeypadRow(buttons=[self._button('payslip', '🔙 بازگشت به لیست'), self._button('start', '🏠 منوی اصلی')])
                ])
                await self._send_text_message(chat_id, message, keyboard)
                return
            
            # Persian month names for caption
            persian_months = {
                1: 'فروردین', 2: 'اردیبهشت', 3: 'خرداد', 4: 'تیر',
                5: 'مرداد', 6: 'شهریور', 7: 'مهر', 8: 'آبان',
                9: 'آذر', 10: 'دی', 11: 'بهمن', 12: 'اسفند'
            }
            month_name = persian_months.get(month, str(month))
            
            # Send confirmation message first
            await self._send_text_message(chat_id, f'📄 در حال ارسال فیش حقوقی {month_name} {year}...')
            
            # Get file extension and create display filename
            import os
            file_ext = os.path.splitext(payslip.file.name)[1] or '.pdf'
            filename = f'payslip_{year}_{month:02d}{file_ext}'
            
            # Send file using async method
            try:
                # Use engine's async _send_file method which properly handles the async call
                await self._send_file(
                    chat_id=chat_id,
                    file_path=file_path,
                    file_name=filename,
                    text=f'💰 فیش حقوقی {month_name} {year}',
                    file_type='File'
                )
                logger.info(f"Sent payslip file to {chat_id}: {year}/{month}")
                
                # ارسال پیام با دکمه‌های بازگشت
                success_message = '✅ فیش حقوقی با موفقیت ارسال شد.'
                keyboard = Keypad(rows=[
                    KeypadRow(buttons=[self._button('payslip', '📋 فیش‌های دیگر'), self._button('start', '🏠 منوی اصلی')])
                ])
                await self._send_text_message(chat_id, success_message, keyboard)
            except Exception as e:
                logger.error(f"Error sending payslip file via rubpy: {e}", exc_info=True)
                message = '❌ خطا در ارسال فایل. لطفاً از طریق پنل وب اقدام کنید.'
                keyboard = Keypad(rows=[
                    KeypadRow(buttons=[self._button('payslip', '🔙 بازگشت به لیست'), self._button('start', '🏠 منوی اصلی')])
                ])
                await self._send_text_message(chat_id, message, keyboard)
                
        except Exception as exc:
            logger.exception(f"Error in _send_payslip_file: {exc}")
            message = '❌ خطا در ارسال فیش حقوقی. لطفاً دوباره تلاش کنید.'
            keyboard = Keypad(rows=[
                KeypadRow(buttons=[self._button('payslip', '🔙 بازگشت به لیست'), self._button('start', '🏠 منوی اصلی')])
            ])
            await self._send_text_message(chat_id, message, keyboard)

    async def _process_connection_code(self, chat_id: str, user: RubikaUser, args: Sequence[str]) -> None:
        if not args:
            await self._handle_connect_button(chat_id, user)
            return
        code_value = args[0]
        
        @sync_to_async(thread_sensitive=True)
        def get_code():
            return RubikaConnectionCode.objects.filter(code=code_value, used=False, expires_at__gt=timezone.now()).select_related('user').first()
        
        code = await get_code()

        if not code:
            message = '❌ کد اتصال نامعتبر، استفاده شده یا منقضی شده است.\n\n💡 لطفاً کد جدیدی از پنل وب دریافت کنید.'
            keyboard = Keypad(rows=[
                KeypadRow(buttons=[self._button('connect', '🔗 راهنمای اتصال'), self._button('start', '🏠 منوی اصلی')])
            ])
            await self._send_text_message(chat_id, message, keyboard)
            return

        previous_username = user.user.username if user.user and user.user != code.user else None
        user.user = code.user
        await sync_to_async(user.save, thread_sensitive=True)(update_fields=['user'])
        await sync_to_async(code.mark_used, thread_sensitive=True)(chat_id=chat_id)

        if previous_username:
            welcome = f'✅ حساب شما از "{previous_username}" به "{code.user.username}" تغییر یافت!\n\n💡 می‌توانید از امکانات ربات استفاده کنید:'
        else:
            welcome = f'✅ حساب شما با موفقیت به "{code.user.username}" متصل شد!\n\n💡 می‌توانید از امکانات ربات استفاده کنید:'
        
        buttons = self._build_command_keyboard(connected=True)
        await self._send_text_message(chat_id, welcome, buttons)

    async def _send_text_message(self, chat_id: str, text: str, inline_keyboard: Optional[Keypad] = None) -> None:
        # This method now needs to be async, but the client call is already handled by rubpy.sync
        try:
            await self.client.send_message(chat_id=chat_id, text=text, inline_keypad=inline_keyboard)
            await sync_to_async(WebhookLog.log_outgoing, thread_sensitive=True)('پیام ارسالی', f'پیام به {chat_id} ارسال شد', {'text': text[:120]})
        except Exception as exc:
            logger.exception("Failed to send message to chat %s", chat_id)
            await sync_to_async(WebhookLog.log_error, thread_sensitive=True)('ارسال پیام ناموفق', str(exc), {'chat_id': chat_id})

    async def _send_file(self, chat_id: str, file_path: str, file_name: str, text: str = '', file_type: str = 'File') -> None:
        """
        ارسال فایل به کاربر به صورت async
        این متد مشابه _send_text_message مستقیماً از await استفاده می‌کند
        """
        try:
            await self.client.send_file(
                chat_id=chat_id,
                file=file_path,
                file_name=file_name,
                text=text,
                type=file_type
            )
            await sync_to_async(WebhookLog.log_outgoing, thread_sensitive=True)(
                'ارسال فایل', 
                f'فایل به {chat_id} ارسال شد', 
                {'file_name': file_name, 'file_type': file_type}
            )
        except Exception as exc:
            logger.exception("Failed to send file to chat %s", chat_id)
            await sync_to_async(WebhookLog.log_error, thread_sensitive=True)(
                'ارسال فایل ناموفق', 
                str(exc), 
                {'chat_id': chat_id, 'file_name': file_name}
            )
            raise

    # ============= Leave Request Handlers =============
    
    async def _start_leave_request(self, chat_id: str, user: RubikaUser) -> None:
        """شروع فرایند درخواست مرخصی"""
        if not user.user:
            message = '⚠️ برای ثبت درخواست مرخصی، ابتدا باید به حساب کاربری خود متصل شوید.\n\n🔗 از دکمه‌های زیر برای اتصال استفاده کنید:'
            buttons = self._build_command_keyboard(connected=False)
            await self._send_text_message(chat_id, message, buttons)
            return
        
        # Create or get leave request state
        @sync_to_async(thread_sensitive=True)
        def init_leave_state():
            from rubika_bot.models import LeaveRequestState
            state, created = LeaveRequestState.objects.get_or_create(rubika_user=user)
            state.reset()
            state.update_step('leave_type')
            return state
        
        await init_leave_state()
        
        # Send leave type selection
        message_lines = [
            '🏖️ درخواست مرخصی جدید',
            '',
            'لطفاً نوع مرخصی خود را انتخاب کنید:',
        ]
        
        # Build leave type keyboard
        leave_types = [
            ('leavetype_regular', '📅 مرخصی استحقاقی'),
            ('leavetype_absence', '❌ غیبت'),
            ('leavetype_hourly', '⏰ مرخصی ساعتی'),
            ('leavetype_sick_leave', '🏥 مرخصی استعلاجی'),
        ]
        
        rows = [
            [leave_types[0], leave_types[1]],
            [leave_types[2], leave_types[3]],
            [('cancel_leave', '❌ انصراف')]
        ]
        
        keypad_rows = [KeypadRow(buttons=[self._button(bid, label) for bid, label in row]) for row in rows]
        keyboard = Keypad(rows=keypad_rows)
        
        await self._send_text_message(chat_id, '\n'.join(message_lines), keyboard)
    
    async def _cancel_leave_request(self, chat_id: str, user: RubikaUser) -> None:
        """لغو فرایند درخواست مرخصی"""
        @sync_to_async(thread_sensitive=True)
        def reset_state():
            from rubika_bot.models import LeaveRequestState
            try:
                state = LeaveRequestState.objects.get(rubika_user=user)
                state.reset()
            except LeaveRequestState.DoesNotExist:
                pass
        
        await reset_state()
        message = '❌ فرایند درخواست مرخصی لغو شد.'
        buttons = self._build_command_keyboard(connected=True)
        await self._send_text_message(chat_id, message, buttons)
    
    async def _cancel_rejection(self, chat_id: str, user: RubikaUser) -> None:
        """لغو فرایند رد درخواست"""
        @sync_to_async(thread_sensitive=True)
        def reset_state():
            from rubika_bot.models import LeaveRequestState
            try:
                state = LeaveRequestState.objects.get(rubika_user=user)
                state.reset()
            except LeaveRequestState.DoesNotExist:
                pass
        
        await reset_state()
        message = '❌ فرایند رد درخواست لغو شد.'
        keyboard = Keypad(rows=[
            KeypadRow(buttons=[self._button('start', '🏠 بازگشت به منوی اصلی')])
        ])
        await self._send_text_message(chat_id, message, keyboard)

    
    async def _handle_leave_type_selection(self, chat_id: str, user: RubikaUser, button_id: str) -> None:
        """پردازش انتخاب نوع مرخصی"""
        leave_type_map = {
            'leavetype_regular': 'regular',
            'leavetype_absence': 'absence',
            'leavetype_hourly': 'hourly',
            'leavetype_sick_leave': 'sick_leave',
        }
        
        leave_type = leave_type_map.get(button_id)
        if not leave_type:
            return
        
        # Update state (optimized with get_or_create_for_user)
        @sync_to_async(thread_sensitive=True)
        def update_state():
            from rubika_bot.models import LeaveRequestState
            state = LeaveRequestState.get_or_create_for_user(user)
            state.update_step('date', {'leave_type': leave_type})
            return state
        
        await update_state()
        
        # Ask for date
        leave_type_labels = {
            'regular': 'مرخصی استحقاقی',
            'absence': 'غیبت',
            'hourly': 'مرخصی ساعتی',
            'sick_leave': 'مرخصی استعلاجی',
        }
        
        message_lines = [
            f'✅ نوع مرخصی: {leave_type_labels[leave_type]}',
            '',
            '📅 لطفاً تاریخ مرخصی را به فرمت شمسی وارد کنید:',
            '',
            'مثال: 1403/09/15',
            '',
            '💡 یا از دکمه زیر برای انصراف استفاده کنید:',
        ]
        
        keyboard = Keypad(rows=[
            KeypadRow(buttons=[self._button('cancel_leave', '❌ انصراف')])
        ])
        
        await self._send_text_message(chat_id, '\n'.join(message_lines), keyboard)
    
    async def _handle_shift_type_selection(self, chat_id: str, user: RubikaUser, button_id: str) -> None:
        """پردازش انتخاب نوع شیفت"""
        shift_type_map = {
            'shifttype_day': 'day',
            'shifttype_day2': 'day2',
            'shifttype_evening': 'evening',
            'shifttype_evening2': 'evening2',
            'shifttype_night': 'night',
            'shifttype_night2': 'night2',
        }
        
        shift_type = shift_type_map.get(button_id)
        if not shift_type:
            return
        
        # Update state
        @sync_to_async(thread_sensitive=True)
        def update_and_get_state():
            from rubika_bot.models import LeaveRequestState
            state = LeaveRequestState.objects.get(rubika_user=user)
            state.update_step('next', {'shift_type': shift_type})
            return state.data.get('leave_type')
        
        leave_type = await update_and_get_state()
        
        # Determine next step based on leave type
        if leave_type == 'regular':
            # Need to select replacement
            await self._ask_for_replacement(chat_id, user)
        elif leave_type == 'hourly':
            # Need to enter hourly times
            await self._ask_for_hourly_times(chat_id, user)
        else:
            # Ask for description
            await self._ask_for_description(chat_id, user)
    
    async def _handle_replacement_selection(self, chat_id: str, user: RubikaUser, button_id: str) -> None:
        """پردازش تایید/رد جایگزین"""
        if button_id == 'confirm_replacement':
            # Get pending replacement from state
            @sync_to_async(thread_sensitive=True)
            def confirm_replacement():
                from rubika_bot.models import LeaveRequestState
                state = LeaveRequestState.objects.get(rubika_user=user)
                pending_replacement_id = state.data.get('pending_replacement_id')
                if pending_replacement_id:
                    state.update_step('description', {'replacement_id': pending_replacement_id})
                    state.data.pop('pending_replacement_id', None)
                    state.save()
                    return True
                return False
            
            success = await confirm_replacement()
            if success:
                await self._ask_for_description(chat_id, user)
            else:
                message = '❌ خطا در تایید جایگزین. لطفاً دوباره تلاش کنید.'
                await self._send_text_message(chat_id, message)
                
        elif button_id == 'reject_replacement':
            # Ask for personnel code again
            message = '🔄 لطفاً کد پرسنلی صحیح جایگزین خود را وارد کنید:'
            keyboard = Keypad(rows=[
                KeypadRow(buttons=[self._button('cancel_leave', '❌ انصراف')])
            ])
            await self._send_text_message(chat_id, message, keyboard)
    
    async def _ask_for_replacement(self, chat_id: str, user: RubikaUser) -> None:
        """درخواست کد پرسنلی جایگزین"""
        # Get user position info
        @sync_to_async(thread_sensitive=True)
        def get_user_position():
            from accounts.models import UserProfile
            try:
                profile = UserProfile.objects.select_related('position').get(user=user.user)
                if profile.position:
                    return profile.position.name
                return None
            except UserProfile.DoesNotExist:
                return None
        
        position_name = await get_user_position()
        
        # Update state to replacement step
        @sync_to_async(thread_sensitive=True)
        def update_state():
            from rubika_bot.models import LeaveRequestState
            state = LeaveRequestState.objects.get(rubika_user=user)
            state.update_step('replacement_code')
        
        await update_state()
        
        # پیام درخواست کد پرسنلی
        message_lines = [
            '👤 انتخاب جایگزین',
            '',
        ]
        
        if position_name:
            message_lines.append(f'📌 سمت شما: {position_name}')
            message_lines.append('')
            message_lines.append('🔍 لطفاً کد پرسنلی جایگزین خود را وارد کنید:')
            message_lines.append('')
            message_lines.append('⚠️ توجه: جایگزین باید هم‌سمت شما باشد')
        else:
            message_lines.append('🔍 لطفاً کد پرسنلی جایگزین خود را وارد کنید:')
        
        message_lines.extend([
            '',
            'مثال: 12345',
            '',
            '💡 یا از دکمه زیر برای انصراف استفاده کنید:',
        ])
        
        keyboard = Keypad(rows=[
            KeypadRow(buttons=[self._button('cancel_leave', '❌ انصراف')])
        ])
        
        await self._send_text_message(chat_id, '\n'.join(message_lines), keyboard)
    
    async def _ask_for_hourly_times(self, chat_id: str, user: RubikaUser) -> None:
        """درخواست ساعات شروع و پایان برای مرخصی ساعتی"""
        @sync_to_async(thread_sensitive=True)
        def update_state():
            from rubika_bot.models import LeaveRequestState
            state = LeaveRequestState.get_or_create_for_user(user)
            state.update_step('hourly_times')
        
        await update_state()
        
        message_lines = [
            '⏰ ساعات مرخصی ساعتی',
            '',
            'لطفاً ساعت شروع و پایان را به فرمت زیر وارد کنید:',
            '',
            'مثال: 08:00-12:00',
            '',
            '💡 یا از دکمه زیر برای انصراف استفاده کنید:',
        ]
        
        keyboard = Keypad(rows=[
            KeypadRow(buttons=[self._button('cancel_leave', '❌ انصراف')])
        ])
        
        await self._send_text_message(chat_id, '\n'.join(message_lines), keyboard)
    
    async def _ask_for_description(self, chat_id: str, user: RubikaUser) -> None:
        """درخواست توضیحات"""
        @sync_to_async(thread_sensitive=True)
        def update_state():
            from rubika_bot.models import LeaveRequestState
            state = LeaveRequestState.get_or_create_for_user(user)
            state.update_step('description')
        
        await update_state()
        
        message_lines = [
            '📝 توضیحات',
            '',
            'لطفاً توضیحات خود را وارد کنید:',
            '',
            '(اختیاری - می‌توانید "رد" یا "skip" بنویسید)',
            '',
            '💡 یا از دکمه زیر برای انصراف استفاده کنید:',
        ]
        
        keyboard = Keypad(rows=[
            KeypadRow(buttons=[self._button('cancel_leave', '❌ انصراف')])
        ])
        
        await self._send_text_message(chat_id, '\n'.join(message_lines), keyboard)
    
    async def _handle_leave_request_input(self, chat_id: str, user: RubikaUser, text: str, leave_state) -> None:
        """پردازش ورودی متنی کاربر در فرایند درخواست مرخصی"""
        step = leave_state.step
        
        if step == 'date':
            await self._process_date_input(chat_id, user, text, leave_state)
        elif step == 'replacement_code':
            await self._process_replacement_code_input(chat_id, user, text, leave_state)
        elif step == 'hourly_times':
            await self._process_hourly_times_input(chat_id, user, text, leave_state)
        elif step == 'description':
            await self._process_description_input(chat_id, user, text, leave_state)
    
    async def _process_replacement_code_input(self, chat_id: str, user: RubikaUser, text: str, leave_state) -> None:
        """پردازش ورودی کد پرسنلی جایگزین"""
        # تبدیل اعداد فارسی و عربی به انگلیسی
        personnel_code = normalize_digits(text.strip())
        
        # Validate and find replacement
        @sync_to_async(thread_sensitive=True)
        def find_replacement():
            from django.contrib.auth.models import User
            from accounts.models import UserProfile
            
            try:
                # Get requester profile
                requester_profile = UserProfile.objects.select_related('position').get(user=user.user)
                
                # Find replacement by personnel code
                try:
                    replacement_profile = UserProfile.objects.select_related(
                        'user', 'position', 'section', 'part'
                    ).get(personnel_code=personnel_code)
                    
                    replacement_user = replacement_profile.user
                    
                    # Check if user is trying to select themselves
                    if replacement_user.id == user.user.id:
                        return None, 'self'
                    
                    # Check if user is active
                    if not replacement_user.is_active:
                        return None, 'inactive'
                    
                    # Check if same position
                    if requester_profile.position and replacement_profile.position:
                        if requester_profile.position.id != replacement_profile.position.id:
                            return {
                                'user': replacement_user,
                                'profile': replacement_profile,
                                'requester_position': requester_profile.position.name,
                                'replacement_position': replacement_profile.position.name,
                            }, 'different_position'
                    
                    # All checks passed
                    return {
                        'user': replacement_user,
                        'profile': replacement_profile,
                        'position': replacement_profile.position.name if replacement_profile.position else 'نامشخص',
                        'section': replacement_profile.section.name if replacement_profile.section else 'نامشخص',
                    }, 'valid'
                    
                except UserProfile.DoesNotExist:
                    return None, 'not_found'
                    
            except UserProfile.DoesNotExist:
                return None, 'no_profile'
        
        result, status = await find_replacement()
        
        # Handle different statuses
        if status == 'self':
            message = '❌ نمی‌توانید خودتان را به عنوان جایگزین انتخاب کنید.\n\nلطفاً کد پرسنلی فرد دیگری را وارد کنید:'
            await self._send_text_message(chat_id, message)
            return
            
        elif status == 'inactive':
            message = '❌ این کاربر غیرفعال است.\n\nلطفاً کد پرسنلی فرد دیگری را وارد کنید:'
            await self._send_text_message(chat_id, message)
            return
            
        elif status == 'not_found':
            message = f'❌ کد پرسنلی "{personnel_code}" یافت نشد.\n\nلطفاً کد صحیح را وارد کنید:'
            await self._send_text_message(chat_id, message)
            return
            
        elif status == 'no_profile':
            message = '❌ پروفایل شما یافت نشد. لطفاً با مدیر سیستم تماس بگیرید.'
            await self._send_text_message(chat_id, message)
            return
            
        elif status == 'different_position':
            # Show warning but allow selection
            replacement_user = result['user']
            full_name = replacement_user.get_full_name() or replacement_user.username
            
            message_lines = [
                '⚠️ هشدار: سمت متفاوت',
                '',
                f'👤 نام: {full_name}',
                f'📌 سمت شما: {result["requester_position"]}',
                f'📌 سمت جایگزین: {result["replacement_position"]}',
                '',
                '❓ آیا مطمئن هستید که این فرد را به عنوان جایگزین انتخاب می‌کنید؟',
            ]
            
            # Save pending replacement
            @sync_to_async(thread_sensitive=True)
            def save_pending():
                from rubika_bot.models import LeaveRequestState
                state = LeaveRequestState.objects.get(rubika_user=user)
                state.data['pending_replacement_id'] = replacement_user.id
                state.save()
            
            await save_pending()
            
            keyboard = Keypad(rows=[
                KeypadRow(buttons=[
                    self._button('confirm_replacement', '✅ بله، تایید'),
                    self._button('reject_replacement', '❌ خیر، اصلاح')
                ]),
                KeypadRow(buttons=[self._button('cancel_leave', '🔙 انصراف')])
            ])
            
            await self._send_text_message(chat_id, '\n'.join(message_lines), keyboard)
            return
            
        elif status == 'valid':
            # Show confirmation
            replacement_user = result['user']
            full_name = replacement_user.get_full_name() or replacement_user.username
            
            message_lines = [
                '✅ جایگزین یافت شد',
                '',
                f'👤 نام: {full_name}',
                f'📌 سمت: {result["position"]}',
                f'🏢 بخش: {result["section"]}',
                '',
                '❓ آیا این فرد صحیح است؟',
            ]
            
            # Save pending replacement
            @sync_to_async(thread_sensitive=True)
            def save_pending():
                from rubika_bot.models import LeaveRequestState
                state = LeaveRequestState.objects.get(rubika_user=user)
                state.data['pending_replacement_id'] = replacement_user.id
                state.save()
            
            await save_pending()
            
            keyboard = Keypad(rows=[
                KeypadRow(buttons=[
                    self._button('confirm_replacement', '✅ بله، تایید'),
                    self._button('reject_replacement', '❌ خیر، اصلاح')
                ]),
                KeypadRow(buttons=[self._button('cancel_leave', '🔙 انصراف')])
            ])
            
            await self._send_text_message(chat_id, '\n'.join(message_lines), keyboard)
    
    async def _process_date_input(self, chat_id: str, user: RubikaUser, text: str, leave_state) -> None:
        """پردازش ورودی تاریخ"""
        import jdatetime
        
        # Validate date format
        try:
            # تبدیل اعداد فارسی و عربی به انگلیسی و حذف فضاها
            date_str = normalize_digits(text.strip()).replace(' ', '').replace('/', '-')
            
            if '-' in date_str:
                parts = date_str.split('-')
            else:
                raise ValueError("فرمت نامعتبر")
            
            if len(parts) != 3:
                raise ValueError("فرمت نامعتبر")
            
            year, month, day = map(int, parts)
            
            # Create jalali date
            jalali_date = jdatetime.date(year, month, day)
            gregorian_date = jalali_date.togregorian()
            
            # Check if date is in the future or today
            today = jdatetime.date.today()
            if jalali_date < today:
                message = '⚠️ تاریخ وارد شده در گذشته است. لطفاً تاریخ معتبری وارد کنید.'
                await self._send_text_message(chat_id, message)
                return
            
        except Exception as e:
            message = '❌ فرمت تاریخ نامعتبر است. لطفاً به فرمت زیر وارد کنید:\n\n1403/09/15\n\nیا 1403-09-15'
            await self._send_text_message(chat_id, message)
            return
        
        # Update state
        @sync_to_async(thread_sensitive=True)
        def update_state():
            from rubika_bot.models import LeaveRequestState
            state = LeaveRequestState.objects.get(rubika_user=user)
            state.update_step('shift_type', {
                'date': gregorian_date.isoformat(),
                'date_jalali': f'{year}/{month:02d}/{day:02d}'
            })
        
        await update_state()
        
        # Ask for shift type
        message_lines = [
            f'✅ تاریخ: {year}/{month:02d}/{day:02d}',
            '',
            '🕐 لطفاً نوع شیفت خود را انتخاب کنید:',
        ]
        
        shift_types = [
            ('shifttype_day', 'روزکار اول'),
            ('shifttype_day2', 'روزکار دوم'),
            ('shifttype_evening', 'عصرکار اول'),
            ('shifttype_evening2', 'عصرکار دوم'),
            ('shifttype_night', 'شبکار اول'),
            ('shifttype_night2', 'شبکار دوم'),
        ]
        
        rows = [
            [shift_types[0], shift_types[1]],
            [shift_types[2], shift_types[3]],
            [shift_types[4], shift_types[5]],
            [('cancel_leave', '❌ انصراف')]
        ]
        
        keypad_rows = [KeypadRow(buttons=[self._button(bid, label) for bid, label in row]) for row in rows]
        keyboard = Keypad(rows=keypad_rows)
        
        await self._send_text_message(chat_id, '\n'.join(message_lines), keyboard)
    
    async def _process_hourly_times_input(self, chat_id: str, user: RubikaUser, text: str, leave_state) -> None:
        """پردازش ورودی ساعات مرخصی ساعتی"""
        import re
        from datetime import time
        
        # تبدیل اعداد فارسی و عربی به انگلیسی
        normalized_text = normalize_digits(text.strip())
        
        # Parse time range (e.g., 08:00-12:00 or 08:00 - 12:00)
        time_pattern = r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})'
        match = re.match(time_pattern, normalized_text)
        
        if not match:
            message = '❌ فرمت ساعت نامعتبر است. لطفاً به فرمت زیر وارد کنید:\n\n08:00-12:00'
            await self._send_text_message(chat_id, message)
            return
        
        try:
            start_hour, start_minute, end_hour, end_minute = map(int, match.groups())
            
            start_time = time(start_hour, start_minute)
            end_time = time(end_hour, end_minute)
            
            if start_time >= end_time:
                message = '⚠️ ساعت پایان باید بعد از ساعت شروع باشد.'
                await self._send_text_message(chat_id, message)
                return
            
            # Calculate hours
            from datetime import datetime, timedelta
            start_dt = datetime.combine(datetime.today(), start_time)
            end_dt = datetime.combine(datetime.today(), end_time)
            hours = int((end_dt - start_dt).total_seconds() / 3600)
            
        except ValueError:
            message = '❌ ساعت وارد شده نامعتبر است.'
            await self._send_text_message(chat_id, message)
            return
        
        # Update state
        @sync_to_async(thread_sensitive=True)
        def update_state():
            from rubika_bot.models import LeaveRequestState
            state = LeaveRequestState.objects.get(rubika_user=user)
            state.update_step('description', {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'leave_hours': hours
            })
        
        await update_state()
        await self._ask_for_description(chat_id, user)
    
    async def _process_description_input(self, chat_id: str, user: RubikaUser, text: str, leave_state) -> None:
        """پردازش ورودی توضیحات و نمایش خلاصه"""
        # Check if user wants to skip
        if text.lower().strip() in ['رد', 'skip', 'pass', '-']:
            description = ''
        else:
            description = text.strip()
        
        # Update state
        @sync_to_async(thread_sensitive=True)
        def update_state():
            from rubika_bot.models import LeaveRequestState
            state = LeaveRequestState.objects.get(rubika_user=user)
            state.update_step('confirm', {'description': description})
            return state.data
        
        data = await update_state()
        
        # Show summary
        await self._show_leave_summary(chat_id, user, data)
    
    async def _show_leave_summary(self, chat_id: str, user: RubikaUser, data: dict) -> None:
        """نمایش خلاصه درخواست مرخصی"""
        leave_type_labels = {
            'regular': 'مرخصی استحقاقی',
            'absence': 'غیبت',
            'hourly': 'مرخصی ساعتی',
            'sick_leave': 'مرخصی استعلاجی',
        }
        
        shift_type_labels = {
            'day': 'روزکار اول',
            'day2': 'روزکار دوم',
            'evening': 'عصرکار اول',
            'evening2': 'عصرکار دوم',
            'night': 'شبکار اول',
            'night2': 'شبکار دوم',
        }
        
        message_lines = [
            '📋 خلاصه درخواست مرخصی',
            '',
            f'📌 نوع: {leave_type_labels.get(data.get("leave_type"), "نامشخص")}',
            f'📅 تاریخ: {data.get("date_jalali", "نامشخص")}',
            f'🕐 شیفت: {shift_type_labels.get(data.get("shift_type"), "نامشخص")}',
        ]
        
        # Add hourly details if applicable
        if data.get('leave_type') == 'hourly':
            message_lines.append(f'⏰ ساعات: {data.get("start_time", "")} تا {data.get("end_time", "")} ({data.get("leave_hours", 0)} ساعت)')
        
        # Add replacement if applicable
        if data.get('replacement_id'):
            @sync_to_async(thread_sensitive=True)
            def get_replacement_name():
                from django.contrib.auth.models import User
                try:
                    rep = User.objects.get(id=data['replacement_id'])
                    return rep.get_full_name() or rep.username
                except User.DoesNotExist:
                    return 'نامشخص'
            
            rep_name = await get_replacement_name()
            message_lines.append(f'👤 جایگزین: {rep_name}')
        
        # Add description if exists
        if data.get('description'):
            message_lines.append(f'📝 توضیحات: {data.get("description")}')
        
        message_lines.extend([
            '',
            '✅ آیا اطلاعات صحیح است؟',
        ])
        
        keyboard = Keypad(rows=[
            KeypadRow(buttons=[
                self._button('confirm_leave', '✅ تایید و ثبت'),
                self._button('cancel_leave', '❌ انصراف')
            ])
        ])
        
        await self._send_text_message(chat_id, '\n'.join(message_lines), keyboard)
    
    async def _handle_leave_confirmation(self, chat_id: str, user: RubikaUser, button_id: str) -> None:
        """پردازش تایید نهایی درخواست مرخصی"""
        if button_id == 'confirm_leave':
            await self._save_leave_request(chat_id, user)
        else:
            await self._cancel_leave_request(chat_id, user)
    
    async def _save_leave_request(self, chat_id: str, user: RubikaUser) -> None:
        """ذخیره درخواست مرخصی در دیتابیس"""
        @sync_to_async(thread_sensitive=True)
        def save_leave():
            from rubika_bot.models import LeaveRequestState
            from leave_reports.models import ShiftReport
            from accounts.models import UserProfile
            from django.contrib.auth.models import User
            from datetime import datetime
            
            try:
                state = LeaveRequestState.objects.select_related('rubika_user', 'rubika_user__user').get(rubika_user=user)
                data = state.data
                
                # Get user profile (optimized with select_related)
                profile = UserProfile.objects.select_related('position', 'section', 'user').get(user=user.user)
                
                # Create leave request
                leave_request = ShiftReport()
                leave_request.user = user.user
                leave_request.leave_type = data['leave_type']
                leave_request.shift_date = datetime.fromisoformat(data['date']).date()
                leave_request.shift_type = data['shift_type']
                leave_request.work_group = profile.group or 'نامشخص'
                leave_request.crate_by = profile
                
                # Add optional fields
                if data.get('description'):
                    leave_request.description = data['description']
                
                if data.get('replacement_id'):
                    leave_request.replacement_person = User.objects.get(id=data['replacement_id'])
                
                if data.get('start_time'):
                    from datetime import time as dt_time
                    leave_request.start_time = dt_time.fromisoformat(data['start_time'])
                if data.get('end_time'):
                    from datetime import time as dt_time
                    leave_request.end_time = dt_time.fromisoformat(data['end_time'])
                if data.get('leave_hours'):
                    leave_request.leave_hours = data['leave_hours']
                
                # Set status
                if leave_request.leave_type in ['absence', 'sick_leave', 'hourly']:
                    leave_request.status = 'pending_approval'
                    leave_request.replacement_approved = True
                else:
                    leave_request.status = 'pending_replacement'
                
                leave_request.save()
                
                # Reset state
                state.reset()
                
                return True, leave_request.id
                
            except Exception as e:
                logger.exception(f"Error saving leave request: {e}")
                return False, str(e)
        
        success, result = await save_leave()
        
        if success:
            message = f'✅ درخواست مرخصی شما با موفقیت ثبت شد!\n\n🎫 شماره درخواست: {result}\n\n📱 می‌توانید وضعیت درخواست خود را از پنل وب سایت پیگیری کنید.'
            keyboard = self._build_command_keyboard(connected=True)
            await self._send_text_message(chat_id, message, keyboard)
        else:
            message = f'❌ خطا در ثبت درخواست:\n{result}\n\nلطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.'
            await self._send_text_message(chat_id, message)

    async def _handle_leave_approval_action(self, chat_id: str, user: RubikaUser, button_id: str) -> None:
        """
        پردازش کلیک روی دکمه‌های تایید یا رد درخواست مرخصی
        فرمت button_id: approve_leave_replacement_123 یا reject_leave_manager_456
        """
        # بررسی اتصال کاربر
        if not user.user:
            keyboard = Keypad(rows=[
                KeypadRow(buttons=[self._button('start', '🏠 بازگشت به منوی اصلی')])
            ])
            await self._send_text_message(
                chat_id, 
                '⚠️ برای انجام این عملیات، ابتدا باید به حساب کاربری خود متصل شوید.',
                keyboard
            )
            return
        
        # Parse button_id
        parts = button_id.split('_')
        if len(parts) < 4:
            keyboard = Keypad(rows=[
                KeypadRow(buttons=[self._button('start', '🏠 بازگشت به منوی اصلی')])
            ])
            await self._send_text_message(chat_id, '❌ فرمت دکمه نامعتبر است.', keyboard)
            return
        
        action = parts[0]  # approve or reject
        # parts[1] is 'leave'
        approval_type = parts[2]  # replacement or manager
        leave_id = parts[3]  # درخواست ID
        
        # دریافت اطلاعات درخواست مرخصی
        @sync_to_async(thread_sensitive=True)
        def get_leave_info():
            from leave_reports.models import ShiftReport
            try:
                leave = ShiftReport.objects.select_related(
                    'user', 'replacement_person', 'final_approver'
                ).get(id=leave_id)
                
                # بررسی دسترسی
                if approval_type == 'replacement':
                    if leave.replacement_person != user.user:
                        return None, 'access_denied'
                    if leave.status != 'pending_replacement':
                        return None, 'invalid_status'
                elif approval_type == 'manager':
                    if not leave.can_be_approved_by(user.user):
                        return None, 'access_denied'
                    if leave.status != 'pending_approval':
                        return None, 'invalid_status'
                else:
                    return None, 'invalid_type'
                
                return leave, 'ok'
                
            except ShiftReport.DoesNotExist:
                return None, 'not_found'
        
        leave_request, status = await get_leave_info()
        
        # بررسی خطاها
        keyboard = Keypad(rows=[
            KeypadRow(buttons=[self._button('start', '🏠 بازگشت به منوی اصلی')])
        ])
        
        if status == 'not_found':
            await self._send_text_message(chat_id, '❌ درخواست مرخصی یافت نشد.', keyboard)
            return
        elif status == 'access_denied':
            await self._send_text_message(chat_id, '⚠️ شما مجاز به انجام این عملیات نیستید.', keyboard)
            return
        elif status == 'invalid_status':
            await self._send_text_message(chat_id, '⚠️ این درخواست قابل پردازش نیست (احتمالاً قبلاً پردازش شده است).', keyboard)
            return
        elif status != 'ok':
            await self._send_text_message(chat_id, '❌ خطای نامشخص در بررسی دسترسی.', keyboard)
            return
        
        # اگر رد باشد، درخواست دلیل رد
        if action == 'reject':
            await self._ask_rejection_reason(chat_id, user, leave_id, approval_type)
            return
        
        # اگر تایید باشد، پردازش تایید
        if action == 'approve':
            await self._process_leave_approval(chat_id, user, leave_request, approval_type)
    
    async def _ask_rejection_reason(self, chat_id: str, user: RubikaUser, leave_id: str, approval_type: str) -> None:
        """درخواست دلیل رد از کاربر"""
        # ذخیره state برای پردازش پاسخ بعدی
        @sync_to_async(thread_sensitive=True)
        def save_rejection_state():
            from rubika_bot.models import LeaveRequestState
            state, _ = LeaveRequestState.objects.get_or_create(rubika_user=user)
            state.step = 'rejection_reason'
            state.data = {
                'leave_id': leave_id,
                'approval_type': approval_type
            }
            state.save()
        
        await save_rejection_state()
        
        message_lines = [
            '📝 دلیل رد درخواست',
            '',
            'لطفاً دلیل رد این درخواست را وارد کنید:',
            '',
            '(این دلیل به درخواست‌دهنده نمایش داده می‌شود)',
        ]
        
        keyboard = Keypad(rows=[
            KeypadRow(buttons=[self._button('cancel_rejection', '❌ انصراف')])
        ])
        
        await self._send_text_message(chat_id, '\n'.join(message_lines), keyboard)
    
    async def _process_leave_approval(self, chat_id: str, user: RubikaUser, leave_request, approval_type: str) -> None:
        """پردازش تایید درخواست مرخصی"""
        @sync_to_async(thread_sensitive=True)
        def approve_leave():
            from django.utils import timezone
            from leave_reports.utils import (
                send_notification_to_manager, 
                send_notification_to_requester_approved
            )
            from rubika_bot.models import WebhookLog
            
            try:
                requester_name = leave_request.user.get_full_name() or leave_request.user.username
                leave_type = leave_request.get_leave_type_display()
                
                if approval_type == 'replacement':
                    # تایید توسط جایگزین
                    leave_request.replacement_approved = True
                    leave_request.replacement_approved_at = timezone.now()
                    leave_request.status = 'pending_approval'
                    leave_request.save()
                    
                    # ثبت لاگ
                    WebhookLog.log_outgoing(
                        title='تایید جایگزینی مرخصی',
                        message=f'{user.user.get_full_name()} درخواست {leave_type} {requester_name} را تایید کرد',
                        data={
                            'leave_id': leave_request.id,
                            'approver': user.user.username,
                            'approval_type': 'replacement',
                            'chat_id': chat_id
                        }
                    )
                    
                    # ارسال نوتیفیکیشن به مدیر و درخواست‌دهنده
                    send_notification_to_manager(leave_request)
                    send_notification_to_requester_approved(leave_request, approved_by_type='replacement')
                    
                    return True, 'تأیید جایگزینی با موفقیت انجام شد. درخواست برای تأیید نهایی مدیر ارسال شد.'
                    
                elif approval_type == 'manager':
                    # تایید نهایی توسط مدیر
                    leave_request.status = 'approved'
                    leave_request.final_approver = user.user.userprofile
                    leave_request.final_approved_at = timezone.now()
                    leave_request.registration = True
                    leave_request.save()
                    
                    # ثبت لاگ
                    WebhookLog.log_outgoing(
                        title='تایید نهایی مرخصی',
                        message=f'{user.user.get_full_name()} درخواست {leave_type} {requester_name} را تایید نهایی کرد',
                        data={
                            'leave_id': leave_request.id,
                            'approver': user.user.username,
                            'approval_type': 'manager',
                            'chat_id': chat_id
                        }
                    )
                    
                    # ارسال نوتیفیکیشن به درخواست‌دهنده
                    send_notification_to_requester_approved(leave_request, approved_by_type='manager')
                    
                    return True, 'درخواست با موفقیت تأیید شد و به درخواست‌دهنده اطلاع داده شد.'
                
                return False, 'نوع تایید نامعتبر است.'
                
            except Exception as e:
                logger.exception(f"Error approving leave: {e}")
                return False, f'خطا در تایید: {str(e)}'
        
        success, message = await approve_leave()
        
        if success:
            keyboard = Keypad(rows=[
                KeypadRow(buttons=[self._button('start', '🏠 بازگشت به منوی اصلی')])
            ])
            await self._send_text_message(chat_id, f'✅ {message}', keyboard)
        else:
            keyboard = Keypad(rows=[
                KeypadRow(buttons=[self._button('start', '🏠 بازگشت به منوی اصلی')])
            ])
            await self._send_text_message(chat_id, f'❌ {message}', keyboard)
    
    async def _process_rejection_reason(self, chat_id: str, user: RubikaUser, text: str, leave_state) -> None:
        """پردازش دلیل رد درخواست مرخصی"""
        rejection_reason = text.strip()
        
        if not rejection_reason:
            await self._send_text_message(chat_id, '⚠️ لطفاً دلیل رد را وارد کنید یا از دکمه انصراف استفاده کنید.')
            return
        
        # دریافت اطلاعات از state
        leave_id = leave_state.data.get('leave_id')
        approval_type = leave_state.data.get('approval_type')
        
        if not leave_id or not approval_type:
            await self._send_text_message(chat_id, '❌ خطا در دریافت اطلاعات درخواست.')
            # Reset state
            @sync_to_async(thread_sensitive=True)
            def reset():
                leave_state.reset()
            await reset()
            return
        
        # پردازش رد درخواست
        @sync_to_async(thread_sensitive=True)
        def reject_leave():
            from leave_reports.models import ShiftReport
            from django.utils import timezone
            from leave_reports.utils import send_notification_to_requester_rejected
            from rubika_bot.models import WebhookLog
            
            try:
                leave_request = ShiftReport.objects.select_related(
                    'user', 'replacement_person'
                ).get(id=leave_id)
                
                # بررسی دسترسی
                if approval_type == 'replacement':
                    if leave_request.replacement_person != user.user:
                        return False, 'access_denied'
                    if leave_request.status != 'pending_replacement':
                        return False, 'invalid_status'
                elif approval_type == 'manager':
                    if not leave_request.can_be_approved_by(user.user):
                        return False, 'access_denied'
                    if leave_request.status != 'pending_approval':
                        return False, 'invalid_status'
                else:
                    return False, 'invalid_type'
                
                requester_name = leave_request.user.get_full_name() or leave_request.user.username
                leave_type = leave_request.get_leave_type_display()
                
                # رد درخواست
                leave_request.status = 'rejected'
                leave_request.rejection_reason = rejection_reason
                leave_request.rejected_by = user.user
                leave_request.rejected_at = timezone.now()
                leave_request.save()
                
                # ثبت لاگ
                WebhookLog.log_outgoing(
                    title=f'رد درخواست مرخصی ({approval_type})',
                    message=f'{user.user.get_full_name()} درخواست {leave_type} {requester_name} را رد کرد. دلیل: {rejection_reason}',
                    data={
                        'leave_id': leave_id,
                        'rejector': user.user.username,
                        'rejection_type': approval_type,
                        'rejection_reason': rejection_reason,
                        'chat_id': chat_id
                    }
                )
                
                # ارسال نوتیفیکیشن به درخواست‌دهنده
                send_notification_to_requester_rejected(leave_request, rejected_by_type=approval_type)
                
                # Reset state
                leave_state.reset()
                
                return True, 'درخواست با موفقیت رد شد و به درخواست‌دهنده اطلاع داده شد.'
                
            except ShiftReport.DoesNotExist:
                return False, 'not_found'
            except Exception as e:
                logger.exception(f"Error rejecting leave: {e}")
                return False, f'خطا: {str(e)}'
        
        success, message = await reject_leave()
        
        if success:
            await self._send_text_message(chat_id, f'✅ {message}')
        elif message == 'access_denied':
            await self._send_text_message(chat_id, '⚠️ شما مجاز به انجام این عملیات نیستید.')
        elif message == 'invalid_status':
            await self._send_text_message(chat_id, '⚠️ این درخواست قابل رد نیست (احتمالاً قبلاً پردازش شده است).')
        elif message == 'not_found':
            await self._send_text_message(chat_id, '❌ درخواست مرخصی یافت نشد.')
        else:
            await self._send_text_message(chat_id, f'❌ {message}')



    # --- Synchronous helper methods ---
    def _build_command_keyboard(self, connected: bool) -> Keypad:
        """ساخت کیبورد اصلی ربات با دکمه‌های مناسب بر اساس وضعیت اتصال کاربر"""
        first_row = [('start', '🏠 منوی اصلی'), ('account', '👤 حساب من')]
        
        if connected:
            # کیبورد برای کاربران متصل
            second_row = [('payslip', '💰 فیش حقوقی'), ('leave_request', '🏖️ مرخصی')]
            third_row = [('help', '❓ راهنما'), ('disconnect', '🔓 قطع اتصال')]
        else:
            # کیبورد برای کاربران غیر متصل
            second_row = [('connect', '🔗 اتصال با کد'), ('sms_connect', '📱 اتصال با پیامک')]
            third_row = [('help', '❓ راهنما')]
        
        rows = [first_row, second_row, third_row]
        keypad_rows = [KeypadRow(buttons=[self._button(button_id, label) for button_id, label in row]) for row in rows]
        return Keypad(rows=keypad_rows)

    @staticmethod
    def _button(button_id: str, label: str):
        # ... (کد این تابع بدون تغییر باقی می‌ماند) ...
        from rubpy.bot.models import Button
        return Button(id=button_id, type=ButtonTypeEnum.SIMPLE, button_text=label)

    def _display_name(self, user: RubikaUser) -> str:
        # ... (کد این تابع بدون تغییر باقی می‌ماند) ...
        if user.first_name:
            return f'{user.first_name} {user.last_name or ""}'.strip()
        return 'کاربر گرامی'

    # ============= SMS Connection Handlers =============
    
    async def _start_sms_connection(self, chat_id: str, user: RubikaUser) -> None:
        """شروع فرایند اتصال از طریق SMS"""
        if user.user:
            message = '⚠️ شما قبلاً به حساب کاربری متصل شده‌اید.\n\nاگر می‌خواهید حساب خود را تغییر دهید، ابتدا از دکمه "قطع اتصال" استفاده کنید.'
            buttons = self._build_command_keyboard(connected=True)
            await self._send_text_message(chat_id, message, buttons)
            return
        
        # Create or get connection request state
        @sync_to_async(thread_sensitive=True)
        def init_connection_state():
            from rubika_bot.models import ConnectionRequestState
            state, created = ConnectionRequestState.objects.get_or_create(rubika_user=user)
            state.reset()
            state.update_step('national_code')
            return state
        
        await init_connection_state()
        
        # Send instructions
        message_lines = [
            '📱 اتصال از طریق پیامک',
            '',
            'برای اتصال به حساب کاربری خود از طریق پیامک، لطفاً کد ملی خود را وارد کنید:',
            '',
            '⚠️ توجه: کد ملی باید 10 رقم باشد.',
        ]
        
        # Build cancel button
        rows = [[('cancel_sms_connect', '❌ انصراف')]]
        keypad_rows = [KeypadRow(buttons=[self._button(bid, label) for bid, label in row]) for row in rows]
        keyboard = Keypad(rows=keypad_rows)
        
        await self._send_text_message(chat_id, '\n'.join(message_lines), keyboard)
    
    async def _cancel_sms_connection(self, chat_id: str, user: RubikaUser) -> None:
        """لغو فرایند اتصال از طریق SMS"""
        @sync_to_async(thread_sensitive=True)
        def reset_state():
            from rubika_bot.models import ConnectionRequestState
            try:
                state = ConnectionRequestState.objects.get(rubika_user=user)
                state.reset()
            except ConnectionRequestState.DoesNotExist:
                pass
        
        await reset_state()
        message = '❌ فرایند اتصال لغو شد.'
        buttons = self._build_command_keyboard(connected=False)
        await self._send_text_message(chat_id, message, buttons)
    
    async def _prompt_paste_connection_code(self, chat_id: str, user: RubikaUser) -> None:
        """درخواست از کاربر برای paste کردن کد اتصال"""
        message_lines = [
            '📋 لطفاً کد اتصال دریافت شده از پیامک را در اینجا paste کنید:',
            '',
            '💡 کد شما 32 کاراکتر است و شبیه این است:',
            '`a1b2c3d4e5f6...`',
            '',
            '⏰ توجه: کد تا 60 دقیقه معتبر است.',
        ]
        keyboard = Keypad(rows=[
            KeypadRow(buttons=[self._button('start', '🏠 بازگشت به منوی اصلی')])
        ])
        await self._send_text_message(chat_id, '\n'.join(message_lines), keyboard)
    
    async def _handle_sms_connection_input(self, chat_id: str, user: RubikaUser, text: str, state) -> None:
        """پردازش ورودی کاربر در فرایند اتصال از طریق SMS"""
        if state.step == 'national_code':
            await self._process_national_code(chat_id, user, text, state)
        elif state.step == 'personnel_code':
            await self._process_personnel_code(chat_id, user, text, state)
    
    async def _process_national_code(self, chat_id: str, user: RubikaUser, national_code: str, state) -> None:
        """پردازش کد ملی"""
        # تبدیل اعداد فارسی و عربی به انگلیسی
        national_code = normalize_digits(national_code.strip())
        
        # Validate national code (should be 10 digits)
        if not national_code.isdigit() or len(national_code) != 10:
            message = '❌ کد ملی نامعتبر است. لطفاً یک کد ملی 10 رقمی وارد کنید.'
            keyboard = Keypad(rows=[
                KeypadRow(buttons=[self._button('cancel_sms_connect', '❌ انصراف'), self._button('start', '🏠 منوی اصلی')])
            ])
            await self._send_text_message(chat_id, message, keyboard)
            return
        
        # Save national code and ask for personnel code
        @sync_to_async(thread_sensitive=True)
        def update_state():
            state.update_step('personnel_code', {'national_code': national_code})
        
        await update_state()
        
        message_lines = [
            '✅ کد ملی ثبت شد.',
            '',
            'اکنون لطفاً کد پرسنلی خود را وارد کنید:',
        ]
        
        # Build cancel button
        rows = [[('cancel_sms_connect', '❌ انصراف')]]
        keypad_rows = [KeypadRow(buttons=[self._button(bid, label) for bid, label in row]) for row in rows]
        keyboard = Keypad(rows=keypad_rows)
        
        await self._send_text_message(chat_id, '\n'.join(message_lines), keyboard)
    
    async def _process_personnel_code(self, chat_id: str, user: RubikaUser, personnel_code: str, state) -> None:
        """پردازش کد پرسنلی و ارسال کد اتصال از طریق SMS"""
        # تبدیل اعداد فارسی و عربی به انگلیسی
        personnel_code = normalize_digits(personnel_code.strip())
        
        # Validate personnel code
        if not personnel_code:
            message = '❌ کد پرسنلی نامعتبر است. لطفاً کد پرسنلی خود را وارد کنید:'
            
            # Build cancel button
            rows = [[('cancel_sms_connect', '❌ انصراف'), ('start', '🏠 منوی اصلی')]]
            keypad_rows = [KeypadRow(buttons=[self._button(bid, label) for bid, label in row]) for row in rows]
            keyboard = Keypad(rows=keypad_rows)
            
            await self._send_text_message(chat_id, message, keyboard)
            return
        
        # Find user by national_code and personnel_code
        @sync_to_async(thread_sensitive=True)
        def find_and_send_code():
            from accounts.models import UserProfile
            from rubika_bot.models import RubikaConnectionCode, WebhookLog
            from rubika_bot.sms_utils import send_connection_code_sms
            
            try:
                national_code = state.data.get('national_code')
                logger.info(f"🔍 جستجوی کاربر - کد ملی: {national_code}, کد پرسنلی: {personnel_code}")
                
                WebhookLog.log_info(
                    'درخواست اتصال SMS',
                    f'جستجوی کاربر با کد ملی {national_code} و کد پرسنلی {personnel_code}',
                    {'chat_id': chat_id, 'national_code': national_code, 'personnel_code': personnel_code}
                )
                
                # جستجوی کاربر: اول با کد پرسنلی، سپس بررسی کد ملی
                # (برخی سیستم‌ها کد ملی را در national_code، برخی در username ذخیره می‌کنند)
                
                # جستجو با national_code
                profile = UserProfile.objects.filter(
                    national_code=national_code,
                    personnel_code=personnel_code
                ).select_related('user').first()
                
                # اگر با national_code پیدا نشد، با username (که ممکن است کد ملی باشد) جستجو کن
                if not profile:
                    logger.info(f"🔄 جستجو با username به عنوان کد ملی...")
                    profile = UserProfile.objects.filter(
                        user__username=national_code,
                        personnel_code=personnel_code
                    ).select_related('user').first()
                
                if not profile:
                    # Debug: جستجوی جداگانه برای یافتن مشکل
                    by_personnel = UserProfile.objects.filter(personnel_code=personnel_code).select_related('user').first()
                    
                    if by_personnel:
                        logger.warning(
                            f"⚠️ کاربر با کد پرسنلی {personnel_code} یافت شد:\n"
                            f"   - Username: {by_personnel.user.username}\n"
                            f"   - National code field: {by_personnel.national_code}\n"
                            f"   - Input national code: {national_code}"
                        )
                    
                    logger.error(f"❌ کاربری با کد ملی {national_code} و کد پرسنلی {personnel_code} یافت نشد")
                    return None, 'کاربری با این کد ملی و کد پرسنلی یافت نشد.'
                
                logger.info(f"✅ کاربر یافت شد: {profile.user.username}, موبایل: {profile.mobile}")
                
                if not profile.mobile:
                    logger.error(f"❌ شماره موبایل برای کاربر {profile.user.username} خالی است")
                    return None, 'شماره موبایل برای این کاربر ثبت نشده است.'
                
                # Generate connection code
                RubikaConnectionCode.objects.filter(user=profile.user, used=False).delete()
                code = RubikaConnectionCode.generate_for_user(profile.user)
                logger.info(f"🔑 کد اتصال تولید شد: {code.code}")
                
                # Send SMS
                logger.info(f"📤 شروع ارسال SMS به {profile.mobile}")
                
                WebhookLog.log_info(
                    'ارسال کد اتصال SMS',
                    f'ارسال کد به شماره {profile.mobile} برای کاربر {profile.user.username}',
                    {'mobile': profile.mobile, 'username': profile.user.username, 'code': code.code[:10] + '...'}
                )
                
                sms_sent = send_connection_code_sms(profile.mobile, code.code)
                
                if sms_sent:
                    logger.info(f"✅ SMS با موفقیت ارسال شد به {profile.mobile}")
                    WebhookLog.log_outgoing(
                        'SMS ارسال شد',
                        f'کد اتصال با موفقیت به {profile.mobile} ارسال شد',
                        {'mobile': profile.mobile, 'username': profile.user.username}
                    )
                    return code.code, None
                else:
                    logger.error(f"❌ خطا در ارسال SMS به {profile.mobile}")
                    WebhookLog.log_error(
                        'خطا در ارسال SMS',
                        f'ارسال کد اتصال به {profile.mobile} ناموفق بود',
                        {'mobile': profile.mobile, 'username': profile.user.username}
                    )
                    return None, 'خطا در ارسال پیامک. لطفاً دوباره تلاش کنید.'
                
            except Exception as e:
                logger.exception(f"💥 Error in find_and_send_code: {e}")
                return None, 'خطایی رخ داده است. لطفاً دوباره تلاش کنید.'
        
        code, error = await find_and_send_code()
        
        if error:
            # Don't reset state - let user try again with correct personnel code
            message = f'❌ {error}\n\nلطفاً کد پرسنلی صحیح خود را وارد کنید:'
            
            # Build cancel button
            rows = [[('cancel_sms_connect', '❌ انصراف')]]
            keypad_rows = [KeypadRow(buttons=[self._button(bid, label) for bid, label in row]) for row in rows]
            keyboard = Keypad(rows=keypad_rows)
            
            await self._send_text_message(chat_id, message, keyboard)
        else:
            # Reset state only on success
            @sync_to_async(thread_sensitive=True)
            def reset_state():
                state.reset()
            
            await reset_state()
            
            message_lines = [
                '✅ پیامک حاوی لینک اتصال برای شما ارسال شد!',
                '',
                '📱 پیامک را بررسی کنید و روی لینک کلیک کنید.',
                '',
                '🔗 با کلیک روی لینک، ربات باز شده و اتصال به صورت خودکار برقرار می‌شود.',
                '',
                '⏰ این لینک تا 60 دقیقه معتبر است.',
            ]
            
            await self._send_text_message(chat_id, '\n'.join(message_lines))


class RubPyIntegrationService:
    _instance: Optional["RubPyIntegrationService"] = None

    def __init__(self) -> None:
        """
        Initialize RubPyIntegrationService with proper async/sync handling.
        
        This method is purely synchronous and safe for Celery workers.
        Client initialization is deferred to _get_or_create_client() which runs
        in an async context when actually needed.
        """
        settings_obj = RubikaBotSettings.get_solo()
        token = settings_obj.get_token_safe()
        if not token:
            raise ValueError("توکن ربات روبیکا در تنظیمات یافت نشد.")

        # Store basic attributes (synchronous, safe)
        self._token = token
        
        # Get proxy URL (synchronous operation)
        proxy_url = ''
        if hasattr(settings_obj, 'build_proxy_url'):
            proxy_url = settings_obj.build_proxy_url()
        if not proxy_url and hasattr(settings, 'RUBIKA_BOT'):
            proxy_url = settings.RUBIKA_BOT.get('PROXY_URL', '')
        self._proxy_url = proxy_url

        # Check if we're in an async context (e.g., Celery worker might have a loop)
        # We always create a new loop in a separate thread to avoid conflicts
        try:
            # Try to get the current event loop (might fail if no loop exists)
            current_loop = asyncio.get_running_loop()
            logger.debug("Existing event loop detected, creating new loop in separate thread")
        except RuntimeError:
            # No running loop, which is fine - we'll create one in a thread
            logger.debug("No existing event loop, creating new loop in separate thread")
        
        # Always create a new event loop in a separate thread
        # This ensures it works in both sync (Celery) and async contexts
        self._loop = asyncio.new_event_loop()
        self._loop_ready = threading.Event()
        self._loop_thread = threading.Thread(
            target=self._run_loop, name="rubpy-event-loop", daemon=True
        )
        self._loop_thread.start()
        self._loop_ready.wait()

        # Client and engine will be initialized lazily via _get_or_create_client()
        self.client: Optional[BotClient] = None
        self.engine: Optional[RubikaBotEngine] = None
        self._client_initialized = False
        self._client_init_lock = threading.Lock()
    
    async def _get_or_create_client(self) -> BotClient:
        """
        Lazy initialization of the BotClient and ProxyConnector.
        
        This method must be called from an async context (within the event loop).
        It creates the ProxyConnector and BotClient only when needed, avoiding
        the "no running event loop" error in Celery workers.
        
        Returns:
            The initialized BotClient instance
        """
        # Double-check locking pattern for thread safety
        if self._client_initialized and self.client is not None:
            return self.client
        
        with self._client_init_lock:
            # Check again after acquiring lock
            if self._client_initialized and self.client is not None:
                return self.client
            
            # Now we're in async context, safe to create ProxyConnector
            connector = None
            if self._proxy_url:
                if ProxyConnector is None:
                    logger.warning("Proxy URL defined but aiohttp_socks is not installed; continuing without proxy.")
                else:
                    try:
                        # This is now safe because we're in an async context
                        connector = ProxyConnector.from_url(self._proxy_url)
                        logger.info("Using SOCKS proxy for Rubika client at %s", self._proxy_url)
                    except Exception as exc:
                        logger.error("Failed to create proxy connector from %s: %s", self._proxy_url, exc, exc_info=True)
            
            # Create BotClient
            self.client = BotClient(
                token=self._token,
                use_webhook=True,
                timeout=BOT_REQUEST_TIMEOUT,
                connector=connector,
            )
            self.engine = RubikaBotEngine(self.client)
            self._register_handlers()
            await self.client.start()
            
            self._client_initialized = True
            logger.info("RubPy client initialized successfully")
            return self.client
    
    def _ensure_client_initialized(self) -> None:
        """
        Ensure the client is initialized before use.
        This is a synchronous wrapper that calls the async initialization.
        """
        if not self._client_initialized or self.client is None:
            self._run_sync(self._get_or_create_client())
    
    # ... (متدهای get_instance, reset, handle_webhook_payload, و ... بدون تغییر باقی می‌مانند) ...
    @classmethod
    def get_instance(cls) -> "RubPyIntegrationService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        if cls._instance:
            try:
                if cls._instance.client is not None:
                    cls._instance._run_sync(cls._instance.client.stop())
            except Exception:
                logger.exception("Failed to stop RubPy client cleanly")
            cls._instance._shutdown_loop()
        cls._instance = None

    def handle_webhook_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Ensure client is initialized before processing
        self._ensure_client_initialized()
        updates = list(self._coerce_updates(payload))
        if not updates:
            WebhookLog.log_warning('وبهوک بدون آپدیت', 'هیچ آپدیتی در payload نبود', payload)
            return {'ok': True, 'processed': 0}
        for update in updates:
            try:
                # Call engine handlers directly instead of process_update
                # process_update doesn't return a coroutine, so we call the async handlers directly
                if isinstance(update, InlineMessage):
                    self._run_sync(self.engine.handle_inline(update))
                elif isinstance(update, Update):
                    self._run_sync(self.engine.handle_update(update))
                else:
                    logger.warning("Unknown update type: %s", type(update))
            except Exception as exc:
                logger.exception("Failed to process update: %s", exc)
                WebhookLog.log_error('خطا در پردازش به‌روزرسانی', str(exc), {'payload': payload})
        return {'ok': True, 'processed': len(updates)}

    def send_text_message(self, chat_id: str, text: str) -> None:
        # Ensure client is initialized before sending
        self._ensure_client_initialized()
        # Use engine's async method instead of client's sync wrapper
        # The engine method properly handles the async call within our event loop
        self._run_sync(self.engine._send_text_message(chat_id, text))

    def update_endpoints(self, webhook_url: str) -> Dict[str, Any]:
        # Ensure client is initialized before updating endpoints
        self._ensure_client_initialized()
        results = {}
        all_ok = True
        for update_type in ("ReceiveUpdate", "ReceiveInlineMessage", "ReceiveQuery"):
            try:
                response = self._run_sync(
                    self.client.update_bot_endpoints(webhook_url, update_type)
                )
                results[update_type] = response
            except Exception as exc:
                results[update_type] = {'status': 'ERROR', 'detail': str(exc)}
                all_ok = False
        return {'ok': all_ok, 'results': results}

    def fetch_webhook_info(self) -> Dict[str, Any]:
        # Ensure client is initialized before fetching info
        self._ensure_client_initialized()
        try:
            result = self._run_sync(self.client._make_request("getBotEndpoint", {}))
            return {'ok': True, 'data': result}
        except APIException as exc:
            return {'ok': False, 'error': exc.status, 'detail': exc.dev_message}
        except Exception as exc:
            return {'ok': False, 'error': str(exc)}

    def _register_handlers(self) -> None:
        # THE HANDLER ITSELF MUST BE ASYNC
        # Note: This method is called from _get_or_create_client() after client is created
        if self.client is None:
            raise RuntimeError("Cannot register handlers: client is not initialized")
        @self.client.on_update()
        async def _generic_handler(bot: BotClient, update: Union[Update, InlineMessage]) -> None:
            close_old_connections()
            try:
                if isinstance(update, InlineMessage):
                    await self.engine.handle_inline(update)
                elif isinstance(update, Update):
                    await self.engine.handle_update(update)
            except Exception as exc:
                logger.exception("Error handling update: %s", exc)
                await sync_to_async(WebhookLog.log_error, thread_sensitive=True)('خطای هندلر', str(exc), {'update': getattr(update, '_raw_payload', {})})
            finally:
                close_old_connections()

    def _coerce_updates(self, payload: Dict[str, Any]) -> Iterable[Union[Update, InlineMessage]]:
        # Ensure client is initialized before parsing updates
        if self.client is None:
            self._ensure_client_initialized()
        if 'update' in payload:
            update = self.client._parse_update(payload['update'])
            if update: setattr(update, "_raw_payload", payload); yield update
        if 'inline_message' in payload:
            # Parse inline message manually since _parse_inline_message may not exist
            try:
                inline_data = payload['inline_message']
                inline = InlineMessage(
                    message_id=_safe_str(inline_data.get('message_id')),
                    text=inline_data.get('text', ''),
                    chat_id=_safe_str(inline_data.get('chat_id')),
                    sender_id=_safe_str(inline_data.get('sender_id')),
                    aux_data=inline_data.get('aux_data'),
                )
                setattr(inline, "_raw_payload", payload)
                yield inline
            except Exception as exc:
                logger.warning("Failed to parse inline_message: %s", exc)
        if 'message' in payload and 'update' not in payload:
            legacy_update = self._from_legacy_message(payload)
            if legacy_update: yield legacy_update
        if 'query' in payload and 'update' not in payload:
            query_update = self._from_legacy_query(payload)
            if query_update: yield query_update

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop_ready.set()
        self._loop.run_forever()

    def _run_sync(self, awaitable: Awaitable[Any]) -> Any:
        """
        Safely run an async coroutine from a sync context (e.g., Celery task).
        
        This method uses run_coroutine_threadsafe to execute the coroutine in
        the service's dedicated event loop thread, making it safe to call from
        synchronous Celery workers.
        
        Args:
            awaitable: The coroutine to execute
            
        Returns:
            The result of the coroutine
            
        Raises:
            RuntimeError: If the event loop is not running or closed
        """
        # Ensure the loop is running and ready
        if not self._loop.is_running():
            raise RuntimeError("Event loop is not running. Service may not be initialized properly.")
        
        try:
            future: Future = asyncio.run_coroutine_threadsafe(awaitable, self._loop)
            return future.result(timeout=300)  # 5 minute timeout for safety
        except RuntimeError as e:
            # Handle case where loop might be closed or not accessible
            logger.error(f"Error running coroutine in event loop: {e}", exc_info=True)
            raise RuntimeError(f"Failed to execute async operation: {e}") from e

    def _shutdown_loop(self) -> None:
        if not hasattr(self, "_loop"):
            return

        if self._loop.is_running():
            def _stop_loop() -> None:
                for task in asyncio.all_tasks():
                    task.cancel()
                self._loop.stop()

            self._loop.call_soon_threadsafe(_stop_loop)
            self._loop_thread.join(timeout=5)

        if not self._loop.is_closed():
            self._loop.close()
    
    # ... (متدهای _from_legacy_message و _from_legacy_query بدون تغییر باقی می‌مانند) ...
    def _from_legacy_message(self, payload: Dict[str, Any]) -> Optional[Update]:
        # Ensure client is initialized before parsing
        if self.client is None:
            self._ensure_client_initialized()
        message_data = payload.get('message', {})
        chat_data = message_data.get('chat', {})
        chat_id = _safe_str(chat_data.get('chat_id') or chat_data.get('id'))
        if not chat_id: return None
        message_dict = {"message_id": _safe_str(message_data.get('message_id')), "text": message_data.get('text'), "sender_id": _safe_str((message_data.get('user') or {}).get('guid')), "aux_data": message_data.get('aux_data'),}
        update_dict = {"type": "NewMessage", "chat_id": chat_id, "new_message": message_dict,}
        parsed = self.client._parse_update(update_dict)
        if parsed: setattr(parsed, "_raw_payload", payload)
        return parsed
    def _from_legacy_query(self, payload: Dict[str, Any]) -> Optional[Update]:
        # Ensure client is initialized before parsing
        if self.client is None:
            self._ensure_client_initialized()
        query_data = payload.get('query', {})
        chat_id = _safe_str(query_data.get('chat_id'))
        if not chat_id: return None
        message_dict = {"message_id": _safe_str(query_data.get('query_id')), "text": "", "sender_id": chat_id, "aux_data": {'button_id': query_data.get('button_id')},}
        update_dict = {"type": "NewMessage", "chat_id": chat_id, "new_message": message_dict,}
        parsed = self.client._parse_update(update_dict)
        if parsed: setattr(parsed, "_raw_payload", payload)
        return parsed