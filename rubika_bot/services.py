# rubika_bot/services.py

from __future__ import annotations

import asyncio
import logging
import threading
from concurrent.futures import Future
from typing import Any, Awaitable, Dict, Iterable, List, Optional, Sequence, Tuple, Union

from asgiref.sync import sync_to_async
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
        await sync_to_async(rubika_user.touch_seen, thread_sensitive=True)()

        if not created:
            attrs_to_update: Dict[str, Any] = {}
            if first_name and rubika_user.first_name != first_name: attrs_to_update['first_name'] = first_name
            if last_name and rubika_user.last_name != last_name: attrs_to_update['last_name'] = last_name
            if attrs_to_update:
                await sync_to_async(RubikaUser.objects.filter(pk=rubika_user.pk).update, thread_sensitive=True)(**attrs_to_update)
                for key, value in attrs_to_update.items():
                    setattr(rubika_user, key, value)
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
        }
        handler = mapping.get(button_id.lower())
        if handler:
            await handler(chat_id, user)
        else:
            # Check if it's a payslip selection button (format: payslip_YYYY_MM)
            if button_id.startswith('payslip_'):
                await self._send_payslip_file(chat_id, user, button_id)
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
        lowered = text.strip().lower()
        display_name = self._display_name(user)
        if lowered.startswith('سلام') or lowered in {'hi', 'hello', 'درود', 'salam'}:
            reply = f'سلام {display_name} عزیز! 👋\n\nخوش اومدی! چطور می‌تونم کمکت کنم؟ 🌟'
        else:
            reply = f'سلام {display_name}! ✅\n\nپیام شما دریافت شد:\n"{text}"'
        await self._send_text_message(chat_id, reply)

    async def _send_welcome(self, chat_id: str, user: RubikaUser) -> None:
        display_name = self._display_name(user)
        message_lines = [f'سلام {display_name} عزیز! 👋', 'به ربات خوش آمدید.']
        buttons = self._build_command_keyboard(connected=bool(user.user))
        if user.user:
            message_lines.append(f'✅ شما قبلاً به اکانت "{user.user.username}" متصل شده‌اید.')
        else:
            message_lines.extend(['\n🔗 برای اتصال به حساب کاربری:', '   `/connect [کد]`'])
        message_lines.append('\n👇 می‌توانید از دکمه‌های زیر استفاده کنید:')
        await self._send_text_message(chat_id, '\n'.join(message_lines), buttons)

    async def _send_help(self, chat_id: str, user: RubikaUser) -> None:
        message = ('📖 راهنمای ربات:\n\n' '🔹 `/start` - شروع کار\n' '🔹 `/connect [کد]` - اتصال\n'
                   '🔹 `/account` - وضعیت\n' '🔹 `/disconnect` - قطع اتصال\n' '🔹 `/help` - راهنما')
        buttons = self._build_command_keyboard(connected=bool(user.user))
        await self._send_text_message(chat_id, message, buttons)

    async def _handle_connect_button(self, chat_id: str, user: RubikaUser) -> None:
        message = '🔗 برای اتصال، کد را از پنل دریافت و دستور زیر را ارسال کنید:\n`/connect [کد]`'
        await self._send_text_message(chat_id, message)

    async def _send_account_status(self, chat_id: str, user: RubikaUser) -> None:
        display_name = self._display_name(user)
        if user.user:
            message = f'📊 وضعیت حساب:\n\n✅ متصل به: `{user.user.username}`\n👤 نام: {display_name}'
        else:
            message = f'📊 وضعیت حساب:\n\n❌ متصل نشده\n👤 نام: {display_name}'
        await self._send_text_message(chat_id, message)

    async def _disconnect_user(self, chat_id: str, user: RubikaUser) -> None:
        if user.user:
            username = user.user.username
            user.user = None
            await sync_to_async(user.save, thread_sensitive=True)(update_fields=['user'])
            message = f'حساب کاربری "{username}" از ربات قطع شد. ❌'
        else:
            message = 'شما به هیچ حساب کاربری متصل نیستید. ⚠️'
        await self._send_text_message(chat_id, message)

    async def _handle_payslip_request(self, chat_id: str, user: RubikaUser) -> None:
        """نمایش لیست فیش‌های حقوقی موجود برای کاربر"""
        if not user.user:
            message = '⚠️ برای دریافت فیش حقوقی، ابتدا باید به حساب کاربری خود متصل شوید.\n\n🔗 از دکمه "اتصال" استفاده کنید.'
            await self._send_text_message(chat_id, message)
            return
        
        # Get user profile and payslips
        @sync_to_async(thread_sensitive=True)
        def get_payslips():
            from accounts.models import UserProfile, Payslip
            try:
                profile = UserProfile.objects.get(user=user.user)
                payslips = list(Payslip.objects.filter(user_profile=profile).order_by('-year', '-month')[:12])
                return profile, payslips
            except UserProfile.DoesNotExist:
                return None, []
        
        profile, payslips = await get_payslips()
        
        if not profile:
            message = '⚠️ پروفایل کاربری شما یافت نشد. لطفاً با پشتیبانی تماس بگیرید.'
            await self._send_text_message(chat_id, message)
            return
        
        if not payslips:
            message = '📭 هیچ فیش حقوقی برای شما ثبت نشده است.'
            await self._send_text_message(chat_id, message)
            return
        
        # Build keyboard with available payslips
        from rubpy.bot.models import Keypad, KeypadRow
        
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
        rows.append([('start', '🔙 بازگشت')])
        
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
        
        # Get payslip from database
        @sync_to_async(thread_sensitive=True)
        def get_payslip():
            from accounts.models import UserProfile, Payslip
            try:
                profile = UserProfile.objects.get(user=user.user)
                payslip = Payslip.objects.get(user_profile=profile, year=year, month=month)
                return payslip
            except (UserProfile.DoesNotExist, Payslip.DoesNotExist):
                return None
        
        payslip = await get_payslip()
        
        if not payslip:
            message = '❌ فیش حقوقی مورد نظر یافت نشد.'
            await self._send_text_message(chat_id, message)
            return
        
        if not payslip.file:
            message = '❌ فایل فیش حقوقی موجود نیست.'
            await self._send_text_message(chat_id, message)
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
                await self._send_text_message(chat_id, message)
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
                # Use _run_sync from RubPyIntegrationService to run async method in the dedicated loop
                def send_file_sync():
                    from rubika_bot.services import RubPyIntegrationService
                    service = RubPyIntegrationService.get_instance()
                    return service._run_sync(
                        service.client.send_file(
                            chat_id=chat_id,
                            file=file_path,
                            file_name=filename,
                            text=f'💰 فیش حقوقی {month_name} {year}',
                            type='File'
                        )
                    )
                
                await sync_to_async(send_file_sync, thread_sensitive=True)()
                logger.info(f"Sent payslip file to {chat_id}: {year}/{month}")
            except Exception as e:
                logger.error(f"Error sending payslip file via rubpy: {e}", exc_info=True)
                message = '❌ خطا در ارسال فایل. لطفاً از طریق پنل وب اقدام کنید.'
                await self._send_text_message(chat_id, message)
                
        except Exception as exc:
            logger.exception(f"Error in _send_payslip_file: {exc}")
            message = '❌ خطا در ارسال فیش حقوقی. لطفاً دوباره تلاش کنید.'
            await self._send_text_message(chat_id, message)

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
            # ... (منطق بررسی کد نامعتبر بدون تغییر باقی می‌ماند) ...
            message = 'کد اتصال نامعتبر، استفاده شده یا منقضی شده است. ❌'
            await self._send_text_message(chat_id, message)
            return

        previous_username = user.user.username if user.user and user.user != code.user else None
        user.user = code.user
        await sync_to_async(user.save, thread_sensitive=True)(update_fields=['user'])
        await sync_to_async(code.mark_used, thread_sensitive=True)(chat_id=chat_id)

        if previous_username:
            welcome = f'حساب شما از "{previous_username}" به "{code.user.username}" تغییر یافت! ✅'
        else:
            welcome = f'حساب شما با موفقیت به "{code.user.username}" متصل شد! ✅'
        await self._send_text_message(chat_id, welcome)

    async def _send_text_message(self, chat_id: str, text: str, inline_keyboard: Optional[Keypad] = None) -> None:
        # This method now needs to be async, but the client call is already handled by rubpy.sync
        try:
            await self.client.send_message(chat_id=chat_id, text=text, inline_keypad=inline_keyboard)
            await sync_to_async(WebhookLog.log_outgoing, thread_sensitive=True)('پیام ارسالی', f'پیام به {chat_id} ارسال شد', {'text': text[:120]})
        except Exception as exc:
            logger.exception("Failed to send message to chat %s", chat_id)
            await sync_to_async(WebhookLog.log_error, thread_sensitive=True)('ارسال پیام ناموفق', str(exc), {'chat_id': chat_id})

    # --- Synchronous helper methods ---
    def _build_command_keyboard(self, connected: bool) -> Keypad:
        # ... (کد این تابع بدون تغییر باقی می‌ماند) ...
        first_row = [('start', '🔄 شروع'), ('account', '📊 وضعیت')]
        second_row = [('connect', '🔗 اتصال')]
        if connected:
            second_row.extend([('payslip', '💰 فیش حقوقی'), ('disconnect', '❌ قطع اتصال')])
        rows = [first_row, second_row, [('help', '📖 راهنما')]]
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


class RubPyIntegrationService:
    _instance: Optional["RubPyIntegrationService"] = None

    def __init__(self) -> None:
        settings_obj = RubikaBotSettings.get_solo()
        if not settings_obj.token:
            raise ValueError("توکن ربات روبیکا در تنظیمات یافت نشد.")

        self._loop = asyncio.new_event_loop()
        self._loop_ready = threading.Event()
        self._loop_thread = threading.Thread(
            target=self._run_loop, name="rubpy-event-loop", daemon=True
        )
        self._loop_thread.start()
        self._loop_ready.wait()

        proxy_url = ''
        if hasattr(settings_obj, 'build_proxy_url'):
            proxy_url = settings_obj.build_proxy_url()
        if not proxy_url and hasattr(settings, 'RUBIKA_BOT'):
            proxy_url = settings.RUBIKA_BOT.get('PROXY_URL', '')
        connector = None
        if proxy_url:
            if ProxyConnector is None:
                logger.warning("Proxy URL defined but aiohttp_socks is not installed; continuing without proxy.")
            else:
                try:
                    connector = ProxyConnector.from_url(proxy_url)
                    logger.info("Using SOCKS proxy for Rubika client at %s", proxy_url)
                except Exception as exc:
                    logger.error("Failed to create proxy connector from %s: %s", proxy_url, exc, exc_info=True)

        try:
            self.client = BotClient(
                token=settings_obj.token,
                use_webhook=True,
                timeout=BOT_REQUEST_TIMEOUT,
                connector=connector,
            )
            self.engine = RubikaBotEngine(self.client)
            self._register_handlers()
            self._run_sync(self.client.start())
        except Exception as exc:
            logger.exception("Unable to start RubPy client: %s", exc)
            self._shutdown_loop()
            raise
    
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
                cls._instance._run_sync(cls._instance.client.stop())
            except Exception:
                logger.exception("Failed to stop RubPy client cleanly")
            cls._instance._shutdown_loop()
        cls._instance = None

    def handle_webhook_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # ... (این متد بدون تغییر باقی می‌ماند) ...
        updates = list(self._coerce_updates(payload))
        if not updates:
            WebhookLog.log_warning('وبهوک بدون آپدیت', 'هیچ آپدیتی در payload نبود', payload)
            return {'ok': True, 'processed': 0}
        for update in updates:
            try:
                self._run_sync(self.client.process_update(update))
            except Exception as exc:
                logger.exception("Failed to process update: %s", exc)
                WebhookLog.log_error('خطا در پردازش به‌روزرسانی', str(exc), {'payload': payload})
        return {'ok': True, 'processed': len(updates)}

    def send_text_message(self, chat_id: str, text: str) -> None:
        # This is now async, but we can call it from a sync context (e.g., signals)
        # by wrapping the call if needed. The engine's method is what we use internally.
        self._run_sync(self.client.send_message(chat_id=chat_id, text=text))

    def update_endpoints(self, webhook_url: str) -> Dict[str, Any]:
        # ... (این متد بدون تغییر باقی می‌ماند) ...
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
        # ... (این متد بدون تغییر باقی می‌ماند) ...
        try:
            result = self._run_sync(self.client._make_request("getBotEndpoint", {}))
            return {'ok': True, 'data': result}
        except APIException as exc:
            return {'ok': False, 'error': exc.status, 'detail': exc.dev_message}
        except Exception as exc:
            return {'ok': False, 'error': str(exc)}

    def _register_handlers(self) -> None:
        # THE HANDLER ITSELF MUST BE ASYNC
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
        # ... (این متد بدون تغییر باقی می‌ماند) ...
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
        future: Future = asyncio.run_coroutine_threadsafe(awaitable, self._loop)
        return future.result()

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
        query_data = payload.get('query', {})
        chat_id = _safe_str(query_data.get('chat_id'))
        if not chat_id: return None
        message_dict = {"message_id": _safe_str(query_data.get('query_id')), "text": "", "sender_id": chat_id, "aux_data": {'button_id': query_data.get('button_id')},}
        update_dict = {"type": "NewMessage", "chat_id": chat_id, "new_message": message_dict,}
        parsed = self.client._parse_update(update_dict)
        if parsed: setattr(parsed, "_raw_payload", payload)
        return parsed