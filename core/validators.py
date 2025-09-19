import os
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from PIL import Image
from typing import List


def validate_file_extension(value: UploadedFile, allowed_extensions: List[str]) -> None:
    """
    اعتبارسنجی پسوند فایل
    """
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(
            f'پسوند فایل مجاز نیست. پسوندهای مجاز: {", ".join(allowed_extensions)}'
        )


def validate_image_file(value: UploadedFile) -> None:
    """
    اعتبارسنجی فایل تصویری
    """
    # بررسی پسوند
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    validate_file_extension(value, allowed_extensions)
    
    # بررسی اندازه فایل (حداکثر 5MB)
    if value.size > 5 * 1024 * 1024:
        raise ValidationError('حجم فایل نباید از 5 مگابایت بیشتر باشد.')
    
    # بررسی صحت فرمت تصویر
    try:
        img = Image.open(value)
        img.verify()
    except Exception:
        raise ValidationError('فایل انتخاب شده یک تصویر معتبر نیست.')
    
    # بازنشانی فایل برای استفاده بعدی
    value.seek(0)


def validate_document_file(value: UploadedFile) -> None:
    """
    اعتبارسنجی فایل سندی (PDF, Word, Excel)
    """
    allowed_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx']
    validate_file_extension(value, allowed_extensions)
    
    # بررسی اندازه فایل (حداکثر 10MB)
    if value.size > 10 * 1024 * 1024:
        raise ValidationError('حجم فایل نباید از 10 مگابایت بیشتر باشد.')


def validate_video_file(value: UploadedFile) -> None:
    """
    اعتبارسنجی فایل ویدیویی
    """
    allowed_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv']
    validate_file_extension(value, allowed_extensions)
    
    # بررسی اندازه فایل (حداکثر 50MB)
    if value.size > 50 * 1024 * 1024:
        raise ValidationError('حجم فایل نباید از 50 مگابایت بیشتر باشد.')


def validate_signature_image(value: UploadedFile) -> None:
    """
    اعتبارسنجی خاص برای تصویر امضا
    """
    # اعتبارسنجی کلی تصویر
    validate_image_file(value)
    
    try:
        img = Image.open(value)
        width, height = img.size
        
        # بررسی نسبت ابعاد (نباید خیلی کشیده باشد)
        if width / height > 4 or height / width > 4:
            raise ValidationError('نسبت ابعاد تصویر امضا مناسب نیست.')
        
        # بررسی حداقل و حداکثر ابعاد
        if width < 100 or height < 50:
            raise ValidationError('ابعاد تصویر امضا خیلی کوچک است (حداقل 100x50 پیکسل).')
        
        if width > 800 or height > 400:
            raise ValidationError('ابعاد تصویر امضا خیلی بزرگ است (حداکثر 800x400 پیکسل).')
            
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        raise ValidationError('خطا در پردازش تصویر امضا.')
    finally:
        value.seek(0)