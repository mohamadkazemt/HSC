# rubika_bot/services.py

"""Integration layer between Django app logic and the RubPy client."""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

from django.db import close_old_connections
from django.utils import timezone
from rubpy.bot.enums import ButtonTypeEnum
from rubpy.bot.models import InlineMessage, Keypad, KeypadRow, Message, Update
from rubpy.exceptions import APIException
from rubpy.sync import BotClient

from .constants import BOT_REQUEST_TIMEOUT
from .models import RubikaBotSettings, RubikaConnectionCode, RubikaUser, WebhookLog

logger = logging.getLogger(__name__)


def _safe_str(value: Any) -> str:
    """Safely convert any value to a string, handling None."""
    return "" if value is None else str(value)


def _extract_button_id(message: Optional[Message]) -> Optional[str]:
    """Extract button_id from various possible locations in aux_data."""
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
    """Encapsulates the high-level bot behaviours triggered by updates."""

    def __init__(self, client: BotClient):
        self.client = client

    def handle_update(self, update: Update) -> None:
        """Process a standard update from RubPy."""
        message = update.new_message or update.updated_message
        if not message:
            return
        chat_id = _safe_str(update.chat_id)
        raw_payload = getattr(update, "_raw_payload", {})
        rubika_user = self._ensure_profile(chat_id, message, raw_payload)
        button_id = _extract_button_id(message)
        text = (message.text or "").strip()

        if button_id:
            self._handle_button(chat_id, button_id, rubika_user)
        elif text.startswith("/"):
            self._handle_command(chat_id, text, rubika_user)
        elif text:
            self._handle_plain_text(chat_id, text, rubika_user)

    def handle_inline(self, inline_update: InlineMessage) -> None:
        """Process an inline message update from RubPy."""
        chat_id = _safe_str(inline_update.chat_id)
        button_id = None
        aux = inline_update.aux_data
        if isinstance(aux, dict):
            button_id = aux.get("button_id")
        elif hasattr(aux, "button_id"):
            button_id = aux.button_id
        if button_id:
            user = RubikaUser.get_or_create_by_chat(chat_id)
            user.touch_seen()
            self._handle_button(chat_id, str(button_id), user)

    def _ensure_profile(self, chat_id: str, message: Message, raw_payload: Dict[str, Any]) -> RubikaUser:
        """Get or create a RubikaUser profile from a message."""
        defaults: Dict[str, Any] = {'metadata': {'raw': raw_payload}}
        first_name, last_name = self._extract_names(raw_payload, message)
        if first_name:
            defaults['first_name'] = first_name
        if last_name:
            defaults['last_name'] = last_name

        rubika_user, created = RubikaUser.objects.get_or_create(chat_id=chat_id, defaults=defaults)
        rubika_user.touch_seen()

        if not created:
            attrs_to_update: Dict[str, Any] = {}
            if first_name and rubika_user.first_name != first_name:
                attrs_to_update['first_name'] = first_name
            if last_name and rubika_user.last_name != last_name:
                attrs_to_update['last_name'] = last_name
            if attrs_to_update:
                RubikaUser.objects.filter(pk=rubika_user.pk).update(**attrs_to_update)
                for key, value in attrs_to_update.items():
                    setattr(rubika_user, key, value)
        return rubika_user

    def _extract_names(self, raw_payload: Dict[str, Any], message: Message) -> Tuple[Optional[str], Optional[str]]:
        """Extract user's first and last name from various payload structures."""
        user_info = {}
        if isinstance(raw_payload, dict):
            user_info = (raw_payload.get('message', {}).get('user') or raw_payload.get('user') or {})
        first_name = user_info.get('first_name')
        last_name = user_info.get('last_name')
        if not first_name and message:
            first_name = getattr(message, 'first_name', None)
            last_name = getattr(message, 'last_name', None)
        return first_name, last_name

    def _handle_button(self, chat_id: str, button_id: str, user: RubikaUser) -> None:
        """Route button clicks to the appropriate handler."""
        mapping = {
            'start': self._send_welcome,
            'help': self._send_help,
            'connect': self._handle_connect_button,
            'disconnect': self._disconnect_user,
            'account': self._send_account_status,
        }
        handler = mapping.get(button_id.lower())
        if handler:
            handler(chat_id, user)
        else:
            logger.debug("Unknown button id %s for chat %s", button_id, chat_id)

    def _handle_command(self, chat_id: str, text: str, user: RubikaUser) -> None:
        """Route slash-commands to the appropriate handler."""
        parts = text.split()
        command = parts[0].lstrip('/').lower()
        args = parts[1:]

        if command == 'help' or command == 'راهنما':
            self._send_help(chat_id, user)
        elif command in {'account', 'status'}:
            self._send_account_status(chat_id, user)
        elif command == 'disconnect':
            self._disconnect_user(chat_id, user)
        elif command == 'connect':
            self._process_connection_code(chat_id, user, args)
        elif command == 'start':
            if args:
                self._process_connection_code(chat_id, user, args)
            else:
                self._send_welcome(chat_id, user)
        else:
            self._handle_plain_text(chat_id, text, user)

    def _handle_plain_text(self, chat_id: str, text: str, user: RubikaUser) -> None:
        """Handle non-command text messages."""
        lowered = text.strip().lower()
        display_name = self._display_name(user)
        if lowered.startswith('سلام') or lowered in {'hi', 'hello', 'درود', 'salam'}:
            reply = f'سلام {display_name} عزیز! 👋\n\nخوش اومدی! چطور می‌تونم کمکت کنم؟ 🌟'
        else:
            reply = f'سلام {display_name}! ✅\n\nپیام شما دریافت شد:\n"{text}"'
        self._send_text_message(chat_id, reply)

    def _send_welcome(self, chat_id: str, user: RubikaUser) -> None:
        """Send the main welcome message with appropriate buttons."""
        display_name = self._display_name(user)
        message_lines = [f'سلام {display_name} عزیز! 👋', 'به ربات خوش آمدید.']
        buttons = self._build_command_keyboard(connected=bool(user.user))
        if user.user:
            message_lines.append(f'✅ شما قبلاً به اکانت "{user.user.username}" متصل شده‌اید.')
        else:
            message_lines.extend([
                '\n🔗 برای اتصال به حساب کاربری:',
                'روش ۱: از پنل وب لینک اتصال را دریافت کنید.',
                'روش ۲: کد اتصال را از پنل دریافت و دستور زیر را ارسال کنید:',
                '   `/connect [کد]`',
            ])
        message_lines.append('\n👇 می‌توانید از دکمه‌های زیر استفاده کنید:')
        self._send_text_message(chat_id, '\n'.join(message_lines), buttons)

    def _send_help(self, chat_id: str, user: RubikaUser) -> None:
        """Send the help message."""
        message = (
            '📖 راهنمای ربات:\n\n'
            '🔹 `/start` - شروع کار با ربات\n'
            '🔹 `/connect [کد]` - اتصال به حساب کاربری\n'
            '🔹 `/account` یا `/status` - مشاهده وضعیت اتصال\n'
            '🔹 `/disconnect` - قطع اتصال از حساب کاربری\n'
            '🔹 `/help` - نمایش این راهنما'
        )
        buttons = self._build_command_keyboard(connected=bool(user.user))
        self._send_text_message(chat_id, message, buttons)

    def _handle_connect_button(self, chat_id: str, user: RubikaUser) -> None:
        """Handle the 'connect' button press."""
        message = (
            '🔗 برای اتصال به حساب کاربری:\n\n'
            'از پنل وب‌سایت یک کد اتصال دریافت کرده و دستور زیر را ارسال کنید:\n'
            '`/connect [کد]`'
        )
        self._send_text_message(chat_id, message)

    def _send_account_status(self, chat_id: str, user: RubikaUser) -> None:
        """Send the user's connection status."""
        display_name = self._display_name(user)
        if user.user:
            message = (
                '📊 وضعیت حساب شما:\n\n'
                f'✅ متصل به: `{user.user.username}`\n'
                f'👤 نام: {display_name}'
            )
        else:
            message = (
                '📊 وضعیت حساب شما:\n\n'
                f'❌ متصل نشده\n'
                f'👤 نام: {display_name}'
            )
        self._send_text_message(chat_id, message)

    def _disconnect_user(self, chat_id: str, user: RubikaUser) -> None:
        """Disconnect a user from their linked account."""
        if user.user:
            username = user.user.username
            user.user = None
            user.save(update_fields=['user'])
            message = f'حساب کاربری "{username}" از ربات قطع شد. ❌'
        else:
            message = 'شما به هیچ حساب کاربری متصل نیستید. ⚠️'
        self._send_text_message(chat_id, message)

    def _process_connection_code(self, chat_id: str, user: RubikaUser, args: Sequence[str]) -> None:
        """Validate a connection code and link the user."""
        if not args:
            self._handle_connect_button(chat_id, user)
            return
        code_value = args[0]
        code = RubikaConnectionCode.objects.filter(
            code=code_value, used=False, expires_at__gt=timezone.now()
        ).select_related('user').first()
        if not code:
            expired_code = RubikaConnectionCode.objects.filter(code=code_value).first()
            if expired_code and expired_code.used:
                message = 'این کد قبلاً استفاده شده است. ❌'
            elif expired_code and expired_code.expires_at and expired_code.expires_at <= timezone.now():
                message = 'کد اتصال منقضی شده است. ❌'
            else:
                message = 'کد اتصال نامعتبر یا وجود ندارد. ❌'
            self._send_text_message(chat_id, message)
            return

        previous_username = user.user.username if user.user and user.user != code.user else None
        user.user = code.user
        user.save(update_fields=['user'])
        code.mark_used(chat_id=chat_id)

        if previous_username:
            welcome = f'حساب شما از "{previous_username}" به "{code.user.username}" تغییر یافت! ✅'
        else:
            welcome = f'حساب شما با موفقیت به "{code.user.username}" متصل شد! ✅'
        self._send_text_message(chat_id, welcome)

    def _send_text_message(self, chat_id: str, text: str, inline_keyboard: Optional[Keypad] = None) -> None:
        """Send a text message using the RubPy client, with logging."""
        try:
            self.client.send_message(chat_id=chat_id, text=text, inline_keypad=inline_keyboard)
            WebhookLog.log_outgoing('پیام ارسالی', f'پیام به {chat_id} ارسال شد', {'text': text[:120]})
        except Exception as exc:
            logger.exception("Failed to send message to chat %s", chat_id)
            WebhookLog.log_error('ارسال پیام ناموفق', str(exc), {'chat_id': chat_id})

    def _build_command_keyboard(self, connected: bool) -> Keypad:
        """Build the main command keyboard based on connection status."""
        first_row = [('start', '🔄 شروع'), ('account', '📊 وضعیت')]
        second_row = [('connect', '🔗 اتصال')]
        if connected:
            second_row.append(('disconnect', '❌ قطع اتصال'))
        rows = [first_row, second_row, [('help', '📖 راهنما')]]

        keypad_rows = [
            KeypadRow(buttons=[self._button(button_id, label) for button_id, label in row]) for row in rows
        ]
        return Keypad(rows=keypad_rows)

    @staticmethod
    def _button(button_id: str, label: str):
        """Create a RubPy Button object."""
        from rubpy.bot.models import Button
        return Button(id=button_id, type=ButtonTypeEnum.SIMPLE, button_text=label)

    def _display_name(self, user: RubikaUser) -> str:
        """Get a display-friendly name for the user."""
        if user.first_name:
            return f'{user.first_name} {user.last_name or ""}'.strip()
        return 'کاربر گرامی'


class RubPyIntegrationService:
    """Singleton-style service providing access to the RubPy client instance."""
    _instance: Optional["RubPyIntegrationService"] = None

    def __init__(self) -> None:
        settings_obj = RubikaBotSettings.get_solo()
        token = settings_obj.token
        if not token:
            raise ValueError("توکن ربات روبیکا در تنظیمات یافت نشد.")
        self.client = BotClient(token=token, use_webhook=True, timeout=BOT_REQUEST_TIMEOUT)
        self.engine = RubikaBotEngine(self.client)
        self._register_handlers()
        try:
            self.client.start()
        except Exception as exc:
            logger.exception("Unable to start RubPy client: %s", exc)
            raise

    @classmethod
    def get_instance(cls) -> "RubPyIntegrationService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        if cls._instance:
            try:
                cls._instance.client.stop()
            except Exception:
                logger.exception("Failed to stop RubPy client cleanly")
        cls._instance = None

    def handle_webhook_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process a raw webhook payload by converting it to RubPy updates."""
        updates = list(self._coerce_updates(payload))
        if not updates:
            WebhookLog.log_warning('وبهوک بدون آپدیت', 'هیچ آپدیتی در payload نبود', payload)
            return {'ok': True, 'processed': 0}

        for update in updates:
            try:
                self.client.process_update(update)
            except Exception as exc:
                logger.exception("Failed to process update: %s", exc)
                WebhookLog.log_error('خطا در پردازش به‌روزرسانی', str(exc), {'payload': payload})
        return {'ok': True, 'processed': len(updates)}

    def send_text_message(self, chat_id: str, text: str) -> None:
        """Public method to send a text message."""
        self.engine._send_text_message(chat_id, text)

    def update_endpoints(self, webhook_url: str) -> Dict[str, Any]:
        """Set the webhook URL for all relevant update types."""
        results = {}
        all_ok = True
        for update_type in ("ReceiveUpdate", "ReceiveInlineMessage", "ReceiveQuery"):
            try:
                response = self.client.update_bot_endpoints(webhook_url, update_type)
                results[update_type] = response
            except Exception as exc:
                results[update_type] = {'status': 'ERROR', 'detail': str(exc)}
                all_ok = False
        return {'ok': all_ok, 'results': results}

    def fetch_webhook_info(self) -> Dict[str, Any]:
        """Get current webhook info from Rubika API."""
        try:
            result = self.client._make_request("getBotEndpoint", {})
            return {'ok': True, 'data': result}
        except APIException as exc:
            return {'ok': False, 'error': exc.status, 'detail': exc.dev_message}
        except Exception as exc:
            return {'ok': False, 'error': str(exc)}

    def _register_handlers(self) -> None:
        """Register a generic handler to process all incoming updates."""
        @self.client.on_update()
        def _generic_handler(bot: BotClient, update: Union[Update, InlineMessage]) -> None:
            close_old_connections()
            try:
                if isinstance(update, InlineMessage):
                    self.engine.handle_inline(update)
                elif isinstance(update, Update):
                    self.engine.handle_update(update)
            except Exception as exc:
                logger.exception("Error handling update: %s", exc)
                WebhookLog.log_error('خطای هندلر', str(exc), {'update': getattr(update, '_raw_payload', {})})
            finally:
                close_old_connections()

    def _coerce_updates(self, payload: Dict[str, Any]) -> Iterable[Union[Update, InlineMessage]]:
        """Attempt to parse various payload formats into RubPy objects."""
        # Standard RubPy update format
        if 'update' in payload:
            update = self.client._parse_update(payload['update'])
            if update:
                setattr(update, "_raw_payload", payload)
                yield update
        # Standard RubPy inline message format
        if 'inline_message' in payload:
            inline = self.client._parse_inline_message(payload['inline_message'])
            if inline:
                setattr(inline, "_raw_payload", payload)
                yield inline
        # Legacy format from old implementation
        if 'message' in payload and 'update' not in payload:
            legacy_update = self._from_legacy_message(payload)
            if legacy_update:
                yield legacy_update
        # Legacy format for queries (button clicks)
        if 'query' in payload and 'update' not in payload:
            query_update = self._from_legacy_query(payload)
            if query_update:
                yield query_update

    def _from_legacy_message(self, payload: Dict[str, Any]) -> Optional[Update]:
        """Convert a legacy message payload to a RubPy Update."""
        message_data = payload.get('message', {})
        chat_data = message_data.get('chat', {})
        chat_id = _safe_str(chat_data.get('chat_id') or chat_data.get('id'))
        if not chat_id:
            return None
        
        message_dict = {
            "message_id": _safe_str(message_data.get('message_id')),
            "text": message_data.get('text'),
            "sender_id": _safe_str((message_data.get('user') or {}).get('guid')),
            "aux_data": message_data.get('aux_data'),
        }
        update_dict = {
            "type": "NewMessage",
            "chat_id": chat_id,
            "new_message": message_dict,
        }
        parsed = self.client._parse_update(update_dict)
        if parsed:
            setattr(parsed, "_raw_payload", payload)
        return parsed

    def _from_legacy_query(self, payload: Dict[str, Any]) -> Optional[Update]:
        """Convert a legacy query payload to a RubPy Update."""
        query_data = payload.get('query', {})
        chat_id = _safe_str(query_data.get('chat_id'))
        if not chat_id:
            return None
            
        # Simulate a message with button data to trigger the handler
        message_dict = {
            "message_id": _safe_str(query_data.get('query_id')),
            "text": "", # Queries don't have text
            "sender_id": chat_id, # Assume sender is the user in the chat
            "aux_data": {'button_id': query_data.get('button_id')},
        }
        update_dict = {
            "type": "NewMessage",
            "chat_id": chat_id,
            "new_message": message_dict,
        }
        parsed = self.client._parse_update(update_dict)
        if parsed:
            setattr(parsed, "_raw_payload", payload)
        return parsed