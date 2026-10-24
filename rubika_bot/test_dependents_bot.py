from unittest.mock import AsyncMock

from asgiref.sync import async_to_sync
from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import Dependent, UserProfile
from rubika_bot.models import RubikaUser
from rubika_bot.services import RubikaBotEngine


class RubikaDependentsBotTests(TestCase):
    def setUp(self):
        self.django_user = User.objects.create_user(
            username="test-employee", first_name="رضا", last_name="محمدی"
        )
        self.profile = UserProfile.objects.create(
            user=self.django_user,
            personnel_code="1001",
            mobile="09120000001",
            address="تهران، خیابان آزادی",
        )
        self.rubika_user = RubikaUser.objects.create(
            chat_id="chat-dep-1", user=self.django_user
        )
        self.engine = RubikaBotEngine(client=object())
        self.engine._send_text_message = AsyncMock()

    def test_keyboard_includes_my_dependents_button(self):
        keyboard = self.engine._build_command_keyboard(connected=True)
        all_button_ids = [
            btn.id
            for row in keyboard.rows
            for btn in row.buttons
        ]
        self.assertIn("my_dependents", all_button_ids)
        self.assertTrue(self.engine._is_employee_only_button("my_dependents"))

    def test_show_my_dependents_unconnected(self):
        unconnected = RubikaUser.objects.create(chat_id="chat-dep-2")
        async_to_sync(self.engine._show_my_dependents)("chat-dep-2", unconnected)

        self.engine._send_text_message.assert_awaited_once()
        sent_text = self.engine._send_text_message.await_args.args[1]
        self.assertIn("حساب کاربری خود را متصل کنید", sent_text)

    def test_show_my_dependents_connected_with_data(self):
        Dependent.objects.create(
            personnel=self.profile,
            first_name="سارا",
            last_name="محمدی",
            national_code="0012345678",
            relationship="فرزند",
        )

        async_to_sync(self.engine._show_my_dependents)("chat-dep-1", self.rubika_user)

        self.engine._send_text_message.assert_awaited_once()
        sent_text = self.engine._send_text_message.await_args.args[1]
        self.assertIn("رضا محمدی", sent_text)
        self.assertIn("تهران، خیابان آزادی", sent_text)
        self.assertIn("سارا محمدی", sent_text)
        self.assertIn("https://miepcoj.ir/d/", sent_text)
