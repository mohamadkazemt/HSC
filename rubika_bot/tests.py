from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch
from .models import RubikaUser, RubikaConnectionCode, RubikaBotSettings
import json
from django.utils import timezone


User = get_user_model()


class WebhookTests(TestCase):
    def setUp(self):
        RubikaBotSettings.get_solo()

    @patch('rubika_bot.services.requests.post')
    def test_text_message_connect_valid(self, mpost):
        u = User.objects.create_user(username='u', password='p')
        code = RubikaConnectionCode.generate_for_user(u)
        payload = {
            'message': {
                'chat': {'id': 123, 'first_name': 'A'},
                'text': f'/connect {code.code}'
            }
        }
        resp = self.client.post(reverse('rubika_bot:webhook'), data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        ru = RubikaUser.objects.get(chat_id='123')
        self.assertEqual(ru.user, u)

    @patch('rubika_bot.services.requests.post')
    def test_text_message_connect_invalid(self, mpost):
        payload = {
            'message': {
                'chat': {'id': 124, 'first_name': 'B'},
                'text': '/connect wrong'
            }
        }
        resp = self.client.post(reverse('rubika_bot:webhook'), data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(RubikaUser.objects.filter(chat_id='124').exists())


class SignalsTests(TestCase):
    @patch('rubika_bot.tasks.send_rubika_message.delay')
    def test_notification_signal_enqueues(self, mdelay):
        from dashboard.models import Notification
        u = User.objects.create_user(username='x', password='p')
        RubikaUser.objects.create(chat_id='555', user=u)
        Notification.objects.create(user=u, message='hello')
        self.assertTrue(mdelay.called)


class SettingsAndUtilitiesTests(TestCase):
    def test_store_token(self):
        s = RubikaBotSettings.get_solo()
        s.token = 'abc'
        s.save()
        self.assertEqual(RubikaBotSettings.get_solo().token, 'abc')