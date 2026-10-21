"""
تست‌های سرویس STT

رونویسی باید در یک پروسهٔ جدا انجام شود تا مدل Whisper (~۵۷۰ مگابایت رم)
داخل worker اصلی باقی نماند؛ در صورت در دسترس نبودن پروسهٔ فرزند، مسیر
درون‌پروسه‌ای باید به‌عنوان جایگزین کار کند.
"""
import json
import os
import tempfile
from unittest.mock import patch

from django.test import TestCase

from core import stt_service


class SttIsolationTests(TestCase):
    def _make_audio_file(self):
        handle, path = tempfile.mkstemp(suffix='.ogg')
        with os.fdopen(handle, 'wb') as fh:
            fh.write(b'fake-audio-bytes')
        self.addCleanup(lambda: os.path.exists(path) and os.unlink(path))
        return path

    def test_transcribe_audio_uses_isolated_process(self):
        audio_path = self._make_audio_file()
        payload = json.dumps({'ok': True, 'text': 'متن رونویسی‌شده'}, ensure_ascii=False)

        with patch.object(stt_service.subprocess, 'run') as run:
            run.return_value = stt_service.subprocess.CompletedProcess(
                args=[], returncode=0, stdout=payload, stderr='',
            )
            result = stt_service.transcribe_audio(audio_path, language='fa')

        self.assertEqual(result, 'متن رونویسی‌شده')
        self.assertTrue(run.called)
        command = run.call_args[0][0]
        self.assertIn('-m', command)
        self.assertIn('core.stt_service', command)
        self.assertIn('--transcribe', command)
        self.assertIn(audio_path, command)

    def test_transcribe_audio_returns_none_for_silent_audio(self):
        audio_path = self._make_audio_file()
        payload = json.dumps({'ok': True, 'text': ''}, ensure_ascii=False)

        with patch.object(stt_service.subprocess, 'run') as run:
            run.return_value = stt_service.subprocess.CompletedProcess(
                args=[], returncode=0, stdout=payload, stderr='',
            )
            with patch.object(stt_service, '_transcribe_with_model') as in_process:
                result = stt_service.transcribe_audio(audio_path, language='fa')

        self.assertIsNone(result)
        # صفر بودن خروجی به معنی خطا نیست؛ نباید به مسیر درون‌پروسه‌ای رفت
        self.assertFalse(in_process.called)

    def test_transcribe_audio_falls_back_in_process_when_isolation_fails(self):
        audio_path = self._make_audio_file()

        with (
            patch.object(stt_service.subprocess, 'run', side_effect=OSError('boom')),
            patch.object(stt_service, '_transcribe_with_model') as in_process,
        ):
            in_process.return_value = ('متن داخل پروسه', None)
            result = stt_service.transcribe_audio(audio_path, language='fa')

        self.assertEqual(result, 'متن داخل پروسه')
        self.assertTrue(in_process.called)

    def test_transcribe_audio_missing_file_returns_none(self):
        result = stt_service.transcribe_audio('/tmp/definitely-missing-audio.ogg')
        self.assertIsNone(result)

    def test_isolated_transcription_reports_failure(self):
        audio_path = self._make_audio_file()

        with patch.object(stt_service.subprocess, 'run') as run:
            run.return_value = stt_service.subprocess.CompletedProcess(
                args=[], returncode=1, stdout='', stderr='boom',
            )
            ok, text = stt_service._transcribe_isolated(audio_path)

        self.assertFalse(ok)
        self.assertIsNone(text)
