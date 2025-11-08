import json
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rubpy.bot.models import Message, MessageId, Update

from .models import RubikaBotSettings, RubikaConnectionCode, RubikaUser
from .services import RubikaBotEngine

User = get_user_model()


class WebhookViewTests(TestCase):
    def setUp(self) -> None:
        settings_obj = RubikaBotSettings.get_solo()
        settings_obj.token = 'dummy-token'
        settings_obj.save()

    @patch('rubika_bot.views.RubPyIntegrationService.get_instance')
    def test_webhook_invokes_service(self, mock_service_factory: MagicMock) -> None:
        stub_service = MagicMock()
        stub_service.handle_webhook_payload.return_value = {'ok': True, 'processed': 1}
        mock_service_factory.return_value = stub_service

        payload = {'message': {'chat': {'chat_id': '1'}, 'text': 'hello'}}
        response = self.client.post(
            reverse('rubika_bot:webhook'),
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_FORWARDED_FOR='127.0.0.1',
        )
        self.assertEqual(response.status_code, 200)
        stub_service.handle_webhook_payload.assert_called_once_with(payload)

    def test_webhook_invalid_json(self) -> None:
        response = self.client.post(
            reverse('rubika_bot:webhook'),
            data='not-json',
            content_type='application/json',
            HTTP_X_FORWARDED_FOR='127.0.0.1',
        )
        self.assertEqual(response.status_code, 400)


class RubikaBotEngineTests(TestCase):
    def setUp(self) -> None:
        self.settings = RubikaBotSettings.get_solo()
        self.settings.token = 'dummy-token'
        self.settings.save()
        self.client_stub = MagicMock()
        self.engine = RubikaBotEngine(self.client_stub)

    def _make_update(self, chat_id: str, text: str, raw_user=None) -> Update:
        message = Message(
            text=text,
            message_id=MessageId(message_id='1'),
            sender_id='user-guid',
        )
        update = Update(
            type='NewMessage',
            chat_id=chat_id,
            client=None,
            new_message=message,
        )
        setattr(update, '_raw_payload', {'message': {'chat': {'chat_id': chat_id}, 'user': raw_user or {}}})
        return update

    def test_connect_command_links_user(self) -> None:
        user = User.objects.create_user(username='john', password='pass')
        code = RubikaConnectionCode.generate_for_user(user)

        update = self._make_update('chat-1', f'/connect {code.code}', raw_user={'first_name': 'Ali'})
        self.engine.handle_update(update)

        rubika_user = RubikaUser.objects.get(chat_id='chat-1')
        self.assertEqual(rubika_user.user, user)
        self.assertEqual(rubika_user.first_name, 'Ali')

    def test_disconnect_button(self) -> None:
        user = User.objects.create_user(username='john', password='pass')
        rubika_user = RubikaUser.objects.create(chat_id='chat-1', user=user)
        update = self._make_update('chat-1', '')
        update.new_message.aux_data = {'button_id': 'disconnect'}
        self.engine.handle_update(update)
        rubika_user.refresh_from_db()
        self.assertIsNone(rubika_user.user)


class SignalsTests(TestCase):
    @patch('rubika_bot.tasks.send_rubika_message.delay')
    def test_notification_signal_enqueues(self, mock_delay: MagicMock) -> None:
        from dashboard.models import Notification

        user = User.objects.create_user(username='x', password='p')
        RubikaUser.objects.create(chat_id='555', user=user)
        Notification.objects.create(user=user, message='hello')
        self.assertTrue(mock_delay.called)


class SettingsTests(TestCase):
    def test_token_persistence(self) -> None:
        settings_obj = RubikaBotSettings.get_solo()
        settings_obj.token = 'secure-token'
        settings_obj.save()
        self.assertEqual(RubikaBotSettings.get_solo().token, 'secure-token')

    def test_connection_code_ttl(self) -> None:
        user = User.objects.create_user(username='ttl', password='p')
        code = RubikaConnectionCode.generate_for_user(user, ttl_minutes=30)
        self.assertGreater(code.expires_at, timezone.now())
