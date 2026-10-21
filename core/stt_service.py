# core/stt_service.py
"""
سرویس تبدیل گفتار به متن (STT) با استفاده از faster-whisper
پشتیبانی از زبان فارسی و انگلیسی
"""
import json
import logging
import os
import subprocess
import sys
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)

# Singleton model instance
_whisper_model = None

# مدل faster-whisper "small" حدود ۵۷۰ مگابایت رم اشغال می‌کند. اگر داخل
# همین پروسهٔ celery worker بارگذاری شود، worker برای همیشه روی سقف رم
# می‌ماند و به swap رانده می‌شود. بنابراین رونویسی در یک پروسهٔ جدا اجرا
# می‌شود تا مدل بعد از هر درخواست آزاد شود.
STT_SUBPROCESS_TIMEOUT_SECONDS = 900

# ریشهٔ پروژه (parent پوشهٔ core) برای اجرای ماژول به‌صورت پروسهٔ فرزند
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_whisper_model(model_size: str = 'small'):
    """
    دریافت مدل faster-whisper (Singleton)

    Args:
        model_size: اندازه مدل (tiny, base, small, medium, large-v3)
                    پیش‌فرض: small (تعادل سرعت و دقت)
                    همچنین مسیر کامل مدل local پشتیبانی می‌شود
    """
    global _whisper_model
    if _whisper_model is None:
        try:
            from faster_whisper import WhisperModel

            # تعیین device و compute_type
            # در سرور از CPU استفاده می‌شود (صرفه‌جویی در منابع)
            device = 'cpu'
            compute_type = 'int8'  # بهینه برای CPU

            # مسیرهای local برای مدل‌های از پیش دانلود شده
            local_model_paths = {
                'tiny': '/var/www/HSC/.cache/huggingface/hub/models--Systran--faster-whisper-tiny/snapshots/main',
                'small': '/var/www/HSC/.cache/huggingface/hub/models--Systran--faster-whisper-small/snapshots/main',
            }
            import os
            model_path = local_model_paths.get(model_size, model_size)
            if not os.path.exists(model_path):
                # اگر مسیر local وجود نداشت، از نام مدل استفاده کن (HuggingFace download)
                model_path = model_size

            logger.info(f"بارگذاری مدل faster-whisper ({model_path}) روی {device}...")
            _whisper_model = WhisperModel(
                model_path,
                device=device,
                compute_type=compute_type,
                cpu_threads=2,  # Match actual CPU cores
            )
            logger.info("مدل faster-whisper با موفقیت بارگذاری شد")
        except ImportError:
            logger.error("faster-whisper نصب نشده است. لطفاً pip install faster-whisper را اجرا کنید.")
            raise
        except Exception as e:
            logger.error(f"خطا در بارگذاری مدل faster-whisper: {e}")
            raise

    return _whisper_model


def _build_transcribe_kwargs(language: str = 'fa', initial_prompt: str = None) -> dict:
    """تنظیمات transcription (accuracy-optimized for small model)"""
    kwargs = {
        'beam_size': 3,  # balance between speed and accuracy
        'patience': 1.0,
        'condition_on_previous_text': True,
        'vad_filter': True,
        'vad_parameters': {
            'min_silence_duration_ms': 500,
        },
    }

    if language and language != 'auto':
        kwargs['language'] = language

    if initial_prompt:
        kwargs['initial_prompt'] = initial_prompt

    return kwargs


def _transcribe_with_model(
    audio_path: str,
    language: str = 'fa',
    initial_prompt: str | None = None,
) -> tuple[str | None, object]:
    """رونویسی با مدل بارگذاری‌شده در همین پروسه (بدون ایزوله‌سازی)"""
    model = get_whisper_model()
    kwargs = _build_transcribe_kwargs(language=language, initial_prompt=initial_prompt)

    segments, info = model.transcribe(audio_path, **kwargs)

    # ترکیب تمام segments
    text_parts = []
    for segment in segments:
        text_parts.append(segment.text.strip())

    full_text = ' '.join(text_parts).strip()

    if not full_text:
        logger.warning("متنی از فایل صوتی استخراج نشد")
        return None, info

    logger.info(
        f"تبدیل موفق: {len(full_text)} کاراکتر, زبان تشخیص داده شده: {info.language} "
        f"({info.language_probability:.2f})"
    )
    return full_text, info


def _transcribe_isolated(
    audio_path: str,
    language: str = 'fa',
    initial_prompt: str | None = None,
) -> tuple[bool, str | None]:
    """
    اجرای رونویسی در یک پروسهٔ جدا

    مدل Whisper حدود ۵۷۰ مگابایت رم می‌گیرد؛ با اجرای آن در پروسهٔ فرزند،
    این رم بعد از پایان رونویسی به سیستم برگردانده می‌شود و worker اصلی سبک
    می‌ماند.

    خروجی: (ok, text)
      - ok=False یعنی اجرای پروسهٔ فرزند ممکن نشد و caller باید به مسیر
        درون‌پروسه‌ای برگردد.
      - ok=True و text خالی یعنی رونویسی انجام شد ولی گفتاری تشخیص داده نشد.
    """
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUNBUFFERED'] = '1'

    command = [
        sys.executable,
        '-m',
        'core.stt_service',
        '--transcribe',
        audio_path,
        '--language',
        language or 'fa',
        '--initial-prompt',
        initial_prompt or '',
    ]

    try:
        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=STT_SUBPROCESS_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as e:
        logger.warning(f"اجرای ایزولهٔ رونویسی ممکن نشد: {e}")
        return False, None

    if completed.returncode != 0:
        logger.warning(
            f"پروسهٔ رونویسی با کد {completed.returncode} خاتمه یافت: "
            f"{(completed.stderr or '').strip()[-500:]}"
        )
        return False, None

    payload = None
    for line in (completed.stdout or '').splitlines():
        line = line.strip()
        if line.startswith('{'):
            payload = line
    if payload is None:
        logger.warning("خروجی نامعتبر از پروسهٔ رونویسی دریافت شد")
        return False, None

    try:
        data = json.loads(payload)
    except ValueError:
        logger.warning("خروجی پروسهٔ رونویسی قابل تفسیر نبود")
        return False, None

    if not data.get('ok'):
        logger.warning(f"رونویسی ایزوله ناموفق بود: {data.get('error')}")
        return False, None

    return True, (data.get('text') or None)


def transcribe_audio(
    audio_path: str,
    language: str = 'fa',
    initial_prompt: str = None,
) -> Optional[str]:
    """
    تبدیل فایل صوتی به متن با استفاده از faster-whisper

    Args:
        audio_path: مسیر کامل فایل صوتی
        language: کد زبان (fa=فارسی, en=انگلیسی, auto=خودکار)
        initial_prompt: راهنمای اولیه برای مدل (بهبود دقت)

    Returns:
        متن تبدیل شده یا None در صورت خطا
    """
    try:
        if not os.path.exists(audio_path):
            logger.error(f"فایل صوتی یافت نشد: {audio_path}")
            return None

        file_size = os.path.getsize(audio_path)
        if file_size == 0:
            logger.error("فایل صوتی خالی است")
            return None

        logger.info(f"شروع تبدیل گفتار به متن: {audio_path} ({file_size} bytes)")

        # مسیر اصلی: پروسهٔ جدا (مدل بعد از رونویسی آزاد می‌شود)
        isolated_ok, text = _transcribe_isolated(
            audio_path,
            language=language,
            initial_prompt=initial_prompt,
        )
        if isolated_ok:
            return text

        # مسیر جایگزین: رونویسی در همین پروسه (سازگاری با محیط‌هایی که
        # اجرای پروسهٔ فرزند در آن‌ها ممکن نیست)
        logger.warning("اجرای ایزوله در دسترس نبود، رونویسی در همین پروسه انجام می‌شود")
        text, _info = _transcribe_with_model(
            audio_path,
            language=language,
            initial_prompt=initial_prompt,
        )
        return text

    except Exception as e:
        logger.error(f"خطا در تبدیل گفتار به متن: {e}")
        return None


def transcribe_voice_message(
    audio_data: bytes,
    file_extension: str = '.ogg',
    language: str = 'fa',
) -> Optional[str]:
    """
    تبدیل داده صوتی (bytes) به متن

    Args:
        audio_data: داده خام فایل صوتی
        file_extension: پسوند فایل (.ogg, .mp3, .wav, .m4a)
        language: کد زبان (fa=فارسی, en=انگلیسی)
    """
    try:
        with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        try:
            result = transcribe_audio(tmp_path, language=language)
            return result
        finally:
            os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"خطا در تبدیل پیام صوتی: {e}")
        return None


# پرامپت‌های راهنما برای بهبود دقت STT
LEAVE_PROMPT_FA = (
    "مرخصی استحقاقی غیبت ساعتی استعلاجی "
    "روزکار عصرکار شبکار "
    "اول دوم "
    "تاریخ امروز فردا پس فردا "
    "ساعت شروع پایان"
)


def _main() -> int:
    """نقطهٔ ورود پروسهٔ فرزند: خروجی JSON روی stdout"""
    import argparse

    parser = argparse.ArgumentParser(description="faster-whisper STT runner")
    parser.add_argument('--transcribe', required=True)
    parser.add_argument('--language', default='fa')
    parser.add_argument('--initial-prompt', default='')
    args = parser.parse_args()

    try:
        text, _info = _transcribe_with_model(
            args.transcribe,
            language=args.language,
            initial_prompt=args.initial_prompt or None,
        )
        payload = {'ok': True, 'text': text or ''}
    except Exception as e:
        payload = {'ok': False, 'error': str(e)}

    sys.stdout.write(json.dumps(payload, ensure_ascii=False))
    sys.stdout.flush()
    return 0 if payload.get('ok') else 1


if __name__ == '__main__':
    raise SystemExit(_main())
