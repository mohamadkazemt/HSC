# core/stt_service.py
"""
سرویس تبدیل گفتار به متن (STT) با استفاده از faster-whisper
پشتیبانی از زبان فارسی و انگلیسی
"""
import os
import logging
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)

# Singleton model instance
_whisper_model = None


def get_whisper_model(model_size: str = 'small'):
    """
    دریافت مدل faster-whisper (Singleton)
    
    Args:
        model_size: اندازه مدل (tiny, base, small, medium, large-v3)
                    پیش‌فرض: small (تعادل سرعت و دقت)
    """
    global _whisper_model
    if _whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            
            # تعیین device و compute_type
            # در سرور از CPU استفاده می‌شود (صرفه‌جویی در منابع)
            device = 'cpu'
            compute_type = 'int8'  # بهینه برای CPU
            
            logger.info(f"بارگذاری مدل faster-whisper ({model_size}) روی {device}...")
            _whisper_model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
                cpu_threads=4,
            )
            logger.info("مدل faster-whisper با موفقیت بارگذاری شد")
        except ImportError:
            logger.error("faster-whisper نصب نشده است. لطفاً pip install faster-whisper را اجرا کنید.")
            raise
        except Exception as e:
            logger.error(f"خطا در بارگذاری مدل faster-whisper: {e}")
            raise
    
    return _whisper_model


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
        
        model = get_whisper_model()
        
        # تنظیمات transcription
        kwargs = {
            'beam_size': 5,
            'best_of': 3,
            'patience': 1.0,
            'condition_on_previous_text': True,
            'vad_filter': True,  # فیلتر سکوت
            'vad_parameters': {
                'min_silence_duration_ms': 500,
            },
        }
        
        if language and language != 'auto':
            kwargs['language'] = language
        
        if initial_prompt:
            kwargs['initial_prompt'] = initial_prompt
        
        segments, info = model.transcribe(audio_path, **kwargs)
        
        # ترکیب تمام segments
        text_parts = []
        for segment in segments:
            text_parts.append(segment.text.strip())
        
        full_text = ' '.join(text_parts).strip()
        
        if not full_text:
            logger.warning("متنی از فایل صوتی استخراج نشد")
            return None
        
        logger.info(f"تبدیل موفق: {len(full_text)} کاراکتر, زبان تشخیص داده شده: {info.language} ({info.language_probability:.2f})")
        return full_text
        
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
        language: کد زبان
    
    Returns:
        متن تبدیل شده یا None در صورت خطا
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
