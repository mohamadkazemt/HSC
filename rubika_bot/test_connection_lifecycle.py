from unittest.mock import patch

from asgiref.sync import async_to_sync
from django.test import SimpleTestCase

from .db import database_sync_to_async
from .tasks import _close_task_database_connections


class TaskCleanupTests(SimpleTestCase):
    """Cleanup is explicit at both operation and Celery task boundaries."""

    def test_database_wrapper_closes_after_operation(self):
        with patch("rubika_bot.db.close_old_connections") as close_old, patch(
            "rubika_bot.db.connections.close_all"
        ) as close_all:
            @database_sync_to_async
            def operation():
                return "ok"

            self.assertEqual(async_to_sync(operation)(), "ok")

        self.assertGreaterEqual(close_old.call_count, 2)
        close_all.assert_called_once_with()

    def test_database_wrapper_closes_after_exception(self):
        with patch("rubika_bot.db.close_old_connections") as close_old, patch(
            "rubika_bot.db.connections.close_all"
        ) as close_all:
            @database_sync_to_async
            def operation():
                raise RuntimeError("isolated failure")

            with self.assertRaises(RuntimeError):
                async_to_sync(operation)()

        self.assertGreaterEqual(close_old.call_count, 2)
        close_all.assert_called_once_with()

    def test_task_cleanup_closes_worker_connections(self):
        with patch("rubika_bot.tasks.close_old_connections") as close_old, patch(
            "rubika_bot.tasks.connections.close_all"
        ) as close_all:
            _close_task_database_connections()

        close_old.assert_called_once_with()
        close_all.assert_called_once_with()
