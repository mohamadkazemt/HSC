import asyncio
import time
from unittest.mock import patch

from django.test import SimpleTestCase

from .services import RubPyIntegrationService


class _FakeRubikaBotSettings:
    """Minimal settings stub so the service can be built without a database."""

    def get_token_safe(self):
        return "test-token"

    def build_proxy_url(self):
        return ""


class RubPyEventLoopStartupTests(SimpleTestCase):
    """The dedicated event loop must be running when the service is handed out.

    Regression: the readiness event was signalled *before* ``run_forever()``
    was entered, so a caller that grabbed the service in that window got
    "Event loop is not running. Service may not be initialized properly." and
    the incoming Rubika webhook was retried instead of processed.
    """

    def _build_service(self, slow_startup_seconds: float = 0.2) -> RubPyIntegrationService:
        real_new_event_loop = asyncio.new_event_loop

        def slow_new_event_loop():
            loop = real_new_event_loop()
            real_run_forever = loop.run_forever

            def slow_run_forever(*args, **kwargs):
                # Simulate a slow loop startup: the loop only becomes running
                # after this delay.
                time.sleep(slow_startup_seconds)
                return real_run_forever(*args, **kwargs)

            loop.run_forever = slow_run_forever
            return loop

        with patch("rubika_bot.services.RubikaBotSettings.get_solo", return_value=_FakeRubikaBotSettings()), patch(
            "asyncio.new_event_loop", side_effect=slow_new_event_loop
        ):
            return RubPyIntegrationService()

    def test_loop_is_running_when_service_is_constructed(self):
        service = self._build_service()
        try:
            self.assertTrue(
                service._loop.is_running(),
                "The RubPy event loop must be running before the service is used.",
            )
        finally:
            service._shutdown_loop()

    def test_run_sync_executes_coroutine_on_a_slow_starting_loop(self):
        service = self._build_service()
        try:
            result = service._run_sync(asyncio.sleep(0, result="ok"))
            self.assertEqual(result, "ok")
        finally:
            service._shutdown_loop()
