from unittest.mock import AsyncMock, patch

from asgiref.sync import async_to_sync
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TransactionTestCase

from rubika_bot.models import LeaveRequestState, RubikaUser
from rubika_bot.services import RubikaBotEngine


class LeaveConfirmationTests(TransactionTestCase):
    """Presses of the "confirm" button must never surface a raw KeyError.

    Regression: once a leave request is saved the state is reset (``data = {}``)
    while the summary message and its confirm button stay in the chat.  Pressing
    it again hit ``data['date']`` and the user received a raw ``'date'`` error.
    """

    def setUp(self):
        self.django_user = User.objects.create_user(username="leave-user", password="x")
        self.rubika_user = RubikaUser.objects.create(chat_id="chat-1", user=self.django_user)
        self.engine = RubikaBotEngine(client=object())
        self.engine._send_text_message = AsyncMock()

    def _confirm(self):
        async_to_sync(self.engine._handle_leave_confirmation)(
            "chat-1", self.rubika_user, "confirm_leave"
        )

    def _sent_text(self):
        self.engine._send_text_message.assert_awaited_once()
        return self.engine._send_text_message.await_args.args[1]

    def test_confirm_on_reset_state_reports_expiry_without_crashing(self):
        state = LeaveRequestState.objects.create(
            rubika_user=self.rubika_user, step="confirm", data={}
        )

        self._confirm()

        state.refresh_from_db()
        self.assertEqual(state.step, "idle")
        self.assertEqual(state.data, {})
        message = self._sent_text()
        self.assertIn("منقضی", message)
        self.assertNotIn("'date'", message)

    def test_confirm_with_invalid_date_reports_expiry_without_crashing(self):
        state = LeaveRequestState.objects.create(
            rubika_user=self.rubika_user,
            step="confirm",
            data={"date": "not-a-date", "leave_type": "regular", "shift_type": "day"},
        )

        self._confirm()

        state.refresh_from_db()
        self.assertEqual(state.step, "idle")
        self.assertIn("نامعتبر", self._sent_text())

    def test_duplicate_report_returns_validation_message_without_traceback(self):
        from accounts.models import UserProfile

        UserProfile.objects.create(user=self.django_user)
        LeaveRequestState.objects.create(
            rubika_user=self.rubika_user,
            step="confirm",
            data={"date": "2026-10-22", "leave_type": "regular", "shift_type": "day"},
        )

        with patch(
            "leave_reports.registration_window.validate_submission_date", return_value=None
        ), patch(
            "leave_reports.models.ShiftReport.save",
            side_effect=ValidationError({"__all__": ["قبلاً گزارش ثبت شده است."]}),
        ), self.assertLogs("rubika_bot.services", level="WARNING") as logs:
            self._confirm()

        message = self._sent_text()
        self.assertIn("قبلاً گزارش ثبت شده است.", message)
        self.assertNotIn("__all__", message)
        self.assertTrue(any("Leave request rejected by validation" in line for line in logs.output))
