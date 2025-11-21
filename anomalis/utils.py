"""
یوتیلیتی‌های کمکی برای اپلیکیشن آنومالی‌ها
شامل فشرده‌سازی تصاویر برای کاهش حجم فضای ذخیره‌سازی
"""
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys


def compress_image(image_file, max_size_mb=1, quality=85, max_dimension=1920):
    """
    فشرده‌سازی تصویر برای کاهش حجم فایل
    
    Args:
        image_file: فایل تصویر آپلود شده
        max_size_mb: حداکثر حجم فایل به مگابایت (پیش‌فرض: 1 مگابایت)
        quality: کیفیت تصویر فشرده شده (1-100، پیش‌فرض: 85)
        max_dimension: حداکثر ابعاد تصویر (پیش‌فرض: 1920 پیکسل)
    
    Returns:
        InMemoryUploadedFile: فایل تصویر فشرده شده
    """
    
    # اگر فایل خالی است، همان را برگردان
    if not image_file:
        return image_file
    
    try:
        # محاسبه حجم فایل به مگابایت
        file_size_mb = image_file.size / (1024 * 1024)
        
        # باز کردن تصویر با Pillow
        img = Image.open(image_file)
        
        # تبدیل تصاویر RGBA به RGB (برای JPG)
        if img.mode in ('RGBA', 'LA', 'P'):
            # ایجاد پس‌زمینه سفید
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # تغییر اندازه تصویر اگر بزرگتر از حد مجاز باشد
        if img.width > max_dimension or img.height > max_dimension:
            # محاسبه نسبت تصویر
            ratio = min(max_dimension / img.width, max_dimension / img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # ذخیره تصویر فشرده شده در حافظه
        output = BytesIO()
        
        # اگر فایل کوچکتر از حد مجاز است و نیازی به تغییر اندازه نداشته
        # فقط یک بار با کیفیت مشخص ذخیره می‌کنیم
        if file_size_mb <= max_size_mb:
            img.save(output, format='JPEG', quality=quality, optimize=True)
        else:
            # تلاش برای فشرده‌سازی با کیفیت‌های مختلف تا به حجم دلخواه برسیم
            current_quality = quality
            while current_quality > 20:
                output.seek(0)
                output.truncate(0)
                
                # ذخیره تصویر با کیفیت مشخص شده
                img.save(
                    output,
                    format='JPEG',
                    quality=current_quality,
                    optimize=True
                )
                
                # بررسی حجم فایل
                output_size_mb = output.tell() / (1024 * 1024)
                
                if output_size_mb <= max_size_mb:
                    break
                
                # کاهش کیفیت برای فشرده‌سازی بیشتر
                current_quality -= 10
        
        output.seek(0)
        
        # تعیین نام فایل
        original_name = image_file.name
        if not original_name.lower().endswith(('.jpg', '.jpeg')):
            name_without_ext = original_name.rsplit('.', 1)[0] if '.' in original_name else original_name
            new_name = f"{name_without_ext}.jpg"
        else:
            new_name = original_name
        
        # ایجاد فایل جدید
        compressed_file = InMemoryUploadedFile(
            output,
            'ImageField',
            new_name,
            'image/jpeg',
            sys.getsizeof(output),
            None
        )
        
        return compressed_file
        
    except Exception as e:
        # در صورت بروز خطا، فایل اصلی را برگردان
        print(f"خطا در فشرده‌سازی تصویر: {str(e)}")
        return image_file


def validate_image_file(image_file):
    """
    اعتبارسنجی فایل تصویر
    
    Args:
        image_file: فایل تصویر آپلود شده
    
    Returns:
        tuple: (bool, str) - (معتبر بودن، پیام خطا)
    """
    
    if not image_file:
        return True, ""
    
    # بررسی حجم فایل (حداکثر 10 مگابایت قبل از فشرده‌سازی)
    max_upload_size = 10 * 1024 * 1024  # 10 MB
    if image_file.size > max_upload_size:
        return False, "حجم تصویر نباید بیشتر از 10 مگابایت باشد"
    
    # بررسی نوع فایل
    valid_content_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
    if hasattr(image_file, 'content_type') and image_file.content_type not in valid_content_types:
        return False, "فقط فایل‌های تصویری (JPG, PNG, GIF, WebP) مجاز هستند"
    
    # بررسی پسوند فایل
    import os
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    ext = os.path.splitext(image_file.name)[1].lower()
    if ext not in valid_extensions:
        return False, "پسوند فایل معتبر نیست"
    
    try:
        # بررسی اینکه فایل واقعاً یک تصویر است
        img = Image.open(image_file)
        img.verify()
        # بازگشت به ابتدای فایل بعد از verify
        image_file.seek(0)
        return True, ""
    except Exception as e:
        return False, f"فایل آپلود شده یک تصویر معتبر نیست: {str(e)}"
