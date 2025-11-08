"""Integration layer between Django app logic and the RubPy client."""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

from django.db import close_old_connections
from django.utils import timezone
import rubpy.filters as rubpy_filters
from rubpy.bot.enums import ButtonTypeEnum, UpdateTypeEnum
from rubpy.bot.models import InlineMessage, Keypad, KeypadRow, Message, Update
from rubpy.exceptions import APIException
from rubpy.sync import BotClient

from .constants import BOT_REQUEST_TIMEOUT, DEEPLINK_TEMPLATE, LOG_CLEANUP_DAYS
from .models import RubikaBotSettings, RubikaConnectionCode, RubikaUser, WebhookLog

logger = logging.getLogger(__name__)

# بعضی نسخه‌های RubPy ماژول filters را با یک شیء سفارشی جایگزین می‌کنند
# که __hash__ ندارد و باعث خطا در Django autoreload می‌شود. اینجا یک
# مقدار hash پیش‌فرض برای کلاس آن تنظیم می‌کنیم.
try:  # pragma: no cover - محافظه‌کارانه
    if getattr(rubpy_filters.__class__, "__hash__", None) is None:
        rubpy_filters.__class__.__hash__ = object.__hash__
except Exception:  # pragma: no cover - اگر در نسخه‌ای متفاوت بود
    pass

try:  # pragma: no cover - مشابه برای rubpy.handlers
    import rubpy.handlers as rubpy_handlers  # type: ignore

    if getattr(rubpy_handlers.__class__, "__hash__", None) is None:
        rubpy_handlers.__class__.__hash__ = object.__hash__
except Exception:
    pass


def _safe_str(value: Any) -> str:
    return "" if value is None else str(value)


def _extract_button_id(message: Optional[Message]) -> Optional[str]:
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
        return _safe_str(aux.button_id)
    except AttributeError:
        return None


class RubikaBotEngine:
    """Encapsulates the high-level bot behaviours triggered by updates."""

    def __init__(self, client: BotClient):
        self.client = client

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def handle_update(self, update: Update) -> None:
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

    def send_text(self, chat_id: str, text: str) -> None:
        try:
            self.client.send_message(chat_id, text)
            WebhookLog.log_outgoing(
                'ارسال پیام',
                f'پیام به {chat_id} ارسال شد',
                {'chat_id': chat_id, 'text': text[:120]},
            )
        except Exception as exc:  # pragma: no cover - network failure paths
            logger.exception("Failed to send message to %s", chat_id)
            WebhookLog.log_error(
                'خطا در ارسال پیام',
                f'ارسال پیام به {chat_id} ناموفق بود',
                {'chat_id': chat_id, 'error': str(exc)},
            )

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _ensure_profile(
        self, chat_id: str, message: Message, raw_payload: Dict[str, Any]
    ) -> RubikaUser:
        defaults: Dict[str, Any] = {'metadata': {'raw': raw_payload}}
        first_name, last_name = self._extract_names(raw_payload, message)
        if first_name:
            defaults['first_name'] = first_name
        if last_name:
            defaults['last_name'] = last_name

        rubika_user = RubikaUser.get_or_create_by_chat(chat_id, defaults=defaults)
        rubika_user.touch_seen()

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

    def _extract_names(
        self, raw_payload: Dict[str, Any], message: Message
    ) -> Tuple[Optional[str], Optional[str]]:
        user_info = {}
        if isinstance(raw_payload, dict):
            user_info = (
                raw_payload.get('message', {}).get('user')
                or raw_payload.get('user')
                or {}
            )
        first_name = user_info.get('first_name')
        last_name = user_info.get('last_name')
        if not first_name and message:
            first_name = getattr(message, 'first_name', None)
            last_name = getattr(message, 'last_name', None)
        return first_name, last_name

    # ------------------------------------------------------------------ #
    # Command and button handlers
    # ------------------------------------------------------------------ #
    def _handle_button(self, chat_id: str, button_id: str, user: RubikaUser) -> None:
        mapping = {
            'start': self._handle_start_button,
            'help': self._handle_help_button,
            'connect': self._handle_connect_button,
            'disconnect': self._handle_disconnect_button,
            'account': self._handle_account_button,
        }
        handler = mapping.get(button_id.lower())
        if handler:
            handler(chat_id, user)
        else:
            logger.debug("Unknown button id %s for chat %s", button_id, chat_id)

    def _handle_command(self, chat_id: str, text: str, user: RubikaUser) -> None:
        parts = text.split()
        command = parts[0].lstrip('/').lower()
        args = parts[1:]

        if command == 'help' or command == 'راهنما':
            self._send_help(chat_id)
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
        lowered = text.strip().lower()
        display_name = self._display_name(user)
        if lowered.startswith('سلام') or lowered in {'hi', 'hello', 'درود', 'salam'}:
            reply = (
                f'سلام {display_name} عزیز! 👋\n\n'
                'خوش اومدی! چطور می‌تونم کمکت کنم؟ 🌟'
            )
        else:
            reply = (
                f'سلام {display_name}! ✅\n\n'
                f'پیام شما دریافت شد:\n"{text}"'
            )
        self._send_text(chat_id, reply)

    # ------------------------------------------------------------------ #
    # Specific button implementations
    # ------------------------------------------------------------------ #
    def _handle_start_button(self, chat_id: str, user: RubikaUser) -> None:
        self._send_welcome(chat_id, user)

    def _handle_help_button(self, chat_id: str, _: RubikaUser) -> None:
        self._send_help(chat_id)

    def _handle_connect_button(self, chat_id: str, user: RubikaUser) -> None:
        message = (
            '🔗 برای اتصال به حساب کاربری:\n\n'
            'روش 1️⃣: از پنل وب لینک اتصال را دریافت کنید\n'
            'روش 2️⃣: از پنل وب کد اتصال را دریافت کنید و دستور زیر را ارسال کنید:\n'
            '   /connect [کد]\n\n'
            '💡 برای دریافت کد، به پنل کاربری خود مراجعه کنید.'
        )
        self._send_text(chat_id, message)

    def _handle_disconnect_button(self, chat_id: str, user: RubikaUser) -> None:
        self._disconnect_user(chat_id, user)

    def _handle_account_button(self, chat_id: str, user: RubikaUser) -> None:
        self._send_account_status(chat_id, user)

    # ------------------------------------------------------------------ #
    # Messaging helpers
    # ------------------------------------------------------------------ #
    def _send_welcome(self, chat_id: str, user: RubikaUser) -> None:
        display_name = self._display_name(user)
        message_lines = [
            f'سلام {display_name} عزیز! 👋',
            'به ربات خوش آمدید.',
        ]
        buttons = self._build_command_keyboard(connected=user.user is not None)
        if user.user:
            message_lines.append(
                f'✅ شما قبلاً به اکانت "{user.user.username}" متصل شده‌اید.'
            )
        else:
            message_lines.extend(
                [
                    '🔗 برای اتصال به حساب کاربری:',
                    'روش 1️⃣: از پنل وب لینک اتصال را دریافت کنید',
                    'روش 2️⃣: از پنل وب کد اتصال را دریافت کنید و دستور زیر را ارسال کنید:',
                    '   /connect [کد]',
                    '💡 برای دریافت کد، به پنل کاربری خود مراجعه کنید.',
                ]
            )
        message = '\n'.join(message_lines)
        self._send_text(chat_id, message, buttons)

    def _send_help(self, chat_id: str) -> None:
        message = (
            '📖 راهنمای ربات:\n\n'
            '🔹 /start - شروع کار با ربات\n'
            '🔹 /connect [کد] - اتصال به حساب کاربری\n'
            '🔹 /account یا /status - مشاهده وضعیت اتصال\n'
            '🔹 /disconnect - قطع اتصال از حساب کاربری\n'
            '🔹 /help - نمایش این راهنما\n'
            '\n💡 برای اتصال به حساب کاربری، ابتدا از پنل وب یک کد اتصال دریافت کنید.'
        )
        buttons = self._build_command_keyboard(connected=False)
        self._send_text(chat_id, message, buttons)

    def _send_account_status(self, chat_id: str, user: RubikaUser) -> None:
        display_name = self._display_name(user)
        if user.user:
            message = (
                '📊 وضعیت حساب شما:\n\n'
                f'✅ متصل به: {user.user.username}\n'
                f'👤 نام: {display_name}\n'
                '\n📌 برای قطع اتصال، دستور /disconnect را ارسال کنید.'
            )
        else:
            message = (
                '📊 وضعیت حساب شما:\n\n'
                f'❌ متصل نشده\n'
                f'👤 نام: {display_name}\n'
                '\n📌 برای اتصال به حساب کاربری، یک کد از پنل دریافت کنید و دستور /connect را ارسال کنید.'
            )
        self._send_text(chat_id, message)

    def _disconnect_user(self, chat_id: str, user: RubikaUser) -> None:
        if user.user:
            username = user.user.username
            user.user = None
            user.save(update_fields=['user'])
            message = (
                f'حساب کاربری "{username}" از ربات قطع شد. ❌\n\n'
                'برای اتصال مجدد، یک کد جدید از پنل دریافت کنید.'
            )
        else:
            message = 'شما قبلاً به هیچ حساب کاربری متصل نیستید. ⚠️'
        self._send_text(chat_id, message)

    def _process_connection_code(
        self, chat_id: str, user: RubikaUser, args: Sequence[str]
    ) -> None:
        if not args:
            self._handle_connect_button(chat_id, user)
            return
        code_value = args[0]
        code = RubikaConnectionCode.objects.filter(
            code=code_value, used=False, expires_at__gt=timezone.now()
        ).select_related('user').first()
        if not code:
            expired_code = RubikaConnectionCode.objects.filter(code=code_value).first()
            if expired_code:
                if expired_code.used:
                    message = 'این کد قبلاً استفاده شده است. ❌\n\nلطفاً کد جدید ایجاد کنید.'
                elif expired_code.expires_at and expired_code.expires_at <= timezone.now():
                    message = 'کد اتصال منقضی شده است. ❌\n\nلطفاً کد جدید ایجاد کنید.'
                else:
                    message = 'کد اتصال نامعتبر است. ❌'
            else:
                message = 'کد اتصال وجود ندارد. ❌\n\nلطفاً از پنل کاربری یک کد معتبر دریافت کنید.'
            self._send_text(chat_id, message)
            return

        previous_username = user.user.username if user.user and user.user != code.user else None
        user.user = code.user
        user.save(update_fields=['user'])
        code.mark_used(chat_id=chat_id)

        if previous_username and previous_username != code.user.username:
            welcome = (
                f'سلام {self._display_name(user)} عزیز! 👋\n\n'
                f'حساب شما از "{previous_username}" به "{code.user.username}" تغییر یافت! ✅'
            )
        else:
            welcome = (
                f'سلام {self._display_name(user)} عزیز! 👋\n\n'
                f'حساب شما با موفقیت متصل شد! ✅\n\nاکانت کاربری: {code.user.username}'
            )
        self._send_text(chat_id, welcome)

    def _send_text(
        self,
        chat_id: str,
        text: str,
        inline_keyboard: Optional[Keypad] = None,
    ) -> None:
        try:
            self.client.send_message(
                chat_id=chat_id,
                text=text,
                inline_keypad=inline_keyboard,
            )
            WebhookLog.log_outgoing(
                'پیام ارسالی',
                f'پیام به {chat_id} ارسال شد',
                {'chat_id': chat_id, 'text': text[:120]},
            )
        except Exception as exc:  # pragma: no cover - network failure paths
            logger.exception("Failed to send message to chat %s", chat_id)
            WebhookLog.log_error(
                'ارسال پیام ناموفق',
                f'ارسال پیام به {chat_id} ناموفق بود',
                {'chat_id': chat_id, 'error': str(exc)},
            )

    def _build_command_keyboard(self, connected: bool) -> Keypad:
        rows: List[List[Tuple[str, str]]] = []
        first_row = [('start', '🔄 شروع'), ('account', '📊 وضعیت')]
        second_row = [('connect', '🔗 اتصال')]
        if connected:
            second_row.append(('disconnect', '❌ قطع اتصال'))

        rows = [
            first_row,
            second_row,
            [('help', '📖 راهنما')],
        ]

        keypad_rows = [
            KeypadRow(
                buttons=[
                    self._button(button_id, label)
                    for button_id, label in row
                ]
            )
            for row in rows
        ]
        return Keypad(rows=keypad_rows, resize_keyboard=True)

    @staticmethod
    def _button(button_id: str, label: str):
        from rubpy.bot.models import Button

        return Button(
            id=button_id,
            type=ButtonTypeEnum.SIMPLE,
            button_text=label,
        )

    def _display_name(self, user: RubikaUser) -> str:
        if user.first_name:
            if user.last_name:
                return f'{user.first_name} {user.last_name}'
            return user.first_name
        return 'کاربر گرامی'


class RubPyIntegrationService:
    """Singleton-style service providing access to the RubPy client instance."""

    _instance: Optional["RubPyIntegrationService"] = None

    def __init__(self) -> None:
        settings_obj = RubikaBotSettings.get_solo()
        token = settings_obj.token
        if not token:
            raise ValueError("Rubika bot token is not configured.")

        self.client = BotClient(
            token=token,
            use_webhook=True,
            timeout=BOT_REQUEST_TIMEOUT,
        )
        self.engine = RubikaBotEngine(self.client)
        self._register_handlers()
        try:
            self.client.start()
        except Exception as exc:  # pragma: no cover - network/network failure
            logger.exception("Unable to start RubPy client: %s", exc)
            raise

    # ------------------------------------------------------------------ #
    # Singleton helpers
    # ------------------------------------------------------------------ #
    @classmethod
    def get_instance(cls) -> "RubPyIntegrationService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        instance = cls._instance
        if instance:
            try:
                instance.client.stop()
            except Exception:  # pragma: no cover - best effort
                logger.exception("Failed to stop RubPy client cleanly")
        cls._instance = None

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def handle_webhook_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        updates = list(self._coerce_updates(payload))
        if not updates:
            WebhookLog.log_warning('وبهوک بدون آپدیت', 'هیچ آپدیتی در payload نبود', payload)
            return {'ok': True, 'processed': 0}

        for update in updates:
            try:
                self.client.process_update(update)
            except Exception as exc:  # pragma: no cover - network failure
                logger.exception("Failed to process update: %s", exc)
                WebhookLog.log_error(
                    'خطا در پردازش به‌روزرسانی',
                    str(exc),
                    {'payload': payload},
                )

        return {'ok': True, 'processed': len(updates)}

    def send_text_message(self, chat_id: str, text: str) -> None:
        self.engine.send_text(chat_id, text)

    def update_endpoints(self, webhook_url: str) -> Dict[str, Any]:
        results = {}
        all_ok = True
        for update_type in (
            "ReceiveUpdate",
            "ReceiveInlineMessage",
            "ReceiveQuery",
            "GetSelectionItem",
            "SearchSelectionItems",
        ):
            try:
                response = self.client.update_bot_endpoints(webhook_url, update_type)
                results[update_type] = response
            except Exception as exc:  # pragma: no cover - network failure
                results[update_type] = {'status': 'ERROR', 'detail': str(exc)}
                all_ok = False
        return {'ok': all_ok, 'results': results}

    def fetch_webhook_info(self) -> Dict[str, Any]:
        try:
            result = self.client._make_request("getBotEndpoint", {})
            return {'ok': True, 'data': result}
        except APIException as exc:
            return {'ok': False, 'error': exc.status, 'detail': exc.dev_message}
        except Exception as exc:  # pragma: no cover
            return {'ok': False, 'error': str(exc)}

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _register_handlers(self) -> None:
        @self.client.on_update()
        def _generic_handler(bot: BotClient, update: Update) -> None:
            close_old_connections()
            try:
                if isinstance(update, InlineMessage):
                    self.engine.handle_inline(update)
                elif isinstance(update, Update):
                    self.engine.handle_update(update)
            except Exception as exc:  # pragma: no cover - handler failure
                logger.exception("Error handling update: %s", exc)
                WebhookLog.log_error(
                    'خطا در پردازش به‌روزرسانی',
                    str(exc),
                    {'update': getattr(update, '_raw_payload', {})},
                )
            finally:
                close_old_connections()

    def _coerce_updates(
        self, payload: Dict[str, Any]
    ) -> Iterable[Union[Update, InlineMessage]]:
        if 'update' in payload:
            update = self.client._parse_update(payload['update'])
            if update:
                setattr(update, "_raw_payload", payload)
                yield update
        if 'inline_message' in payload:
            inline_payload = payload['inline_message']
            inline = InlineMessage(
                sender_id=_safe_str(inline_payload.get('sender_id')),
                text=inline_payload.get('text'),
                message_id=_safe_str(inline_payload.get('message_id')),
                chat_id=_safe_str(
                    inline_payload.get('chat_id') or inline_payload.get('chat_guid')
                ),
                file=inline_payload.get('file'),
                location=inline_payload.get('location'),
                aux_data=inline_payload.get('aux_data'),
                client=self.client,
            )
            setattr(inline, "_raw_payload", payload)
            yield inline
        if 'message' in payload:
            legacy_update = self._from_legacy_message(payload)
            if legacy_update:
                yield legacy_update
        if 'query' in payload:
            query_update = self._from_legacy_query(payload)
            if query_update:
                yield query_update

    def _from_legacy_message(self, payload: Dict[str, Any]) -> Optional[Update]:
        message = payload.get('message', {})
        chat = message.get('chat', {})
        chat_id = (
            chat.get('chat_id')
            or chat.get('id')
            or message.get('chat_id')
            or message.get('chat_guid')
        )
        if not chat_id:
            return None
        message_dict = {
            "message_id": _safe_str(
                message.get('message_id') or message.get('msg_id') or ""
            ),
            "text": message.get('text'),
            "sender_id": _safe_str(
                (message.get('user') or {}).get('guid') or message.get('user_guid') or ""
            ),
            "aux_data": message.get('aux_data'),
        }
        update_dict = {
            "type": UpdateTypeEnum.NewMessage,
            "chat_id": chat_id,
            "new_message": message_dict,
        }
        parsed = self.client._parse_update(update_dict)
        if parsed:
            setattr(parsed, "_raw_payload", payload)
            return parsed
        return None

    def _from_legacy_query(self, payload: Dict[str, Any]) -> InlineMessage:
        query = payload.get('query', {})
        inline = InlineMessage(
            sender_id=_safe_str(query.get('chat_id')),
            text="",
            message_id=_safe_str(query.get('query_id')),
            chat_id=_safe_str(query.get('chat_id') or query.get('object_guid')),
            aux_data={'button_id': query.get('button_id')},
            client=self.client,
        )
        setattr(inline, "_raw_payload", payload)
        return inline


__all__ = ['RubPyIntegrationService', 'RubikaBotEngine']
