"""
اسکریپت بهینه‌سازی تصاویر موجود در دیتابیس
این اسکریپت تمام تصاویر آنومالی‌های موجود را فشرده می‌کند

نحوه اجرا:
python manage.py shell < anomalis/optimize_existing_images.py

یا:
python manage.py shell
>>> exec(open('anomalis/optimize_existing_images.py').read())
"""

from anomalis.models import Anomaly
from anomalis.utils import compress_image
from django.core.files.base import File
import os
from pathlib import Path


def optimize_existing_images():
    """
    فشرده‌سازی تصاویر موجود در دیتابیس
    """
    print("=" * 50)
    print("شروع بهینه‌سازی تصاویر موجود")
    print("=" * 50)
    
    # دریافت تمام آنومالی‌هایی که تصویر دارند
    anomalies_with_images = Anomaly.objects.exclude(image='').exclude(image__isnull=True)
    total_count = anomalies_with_images.count()
    
    print(f"\nتعداد کل آنومالی‌ها با تصویر: {total_count}")
    
    if total_count == 0:
        print("هیچ تصویری برای بهینه‌سازی یافت نشد.")
        return
    
    # پرسش تأیید
    confirm = input(f"\nآیا می‌خواهید {total_count} تصویر را بهینه‌سازی کنید؟ (yes/no): ")
    if confirm.lower() not in ['yes', 'y', 'بله']:
        print("عملیات لغو شد.")
        return
    
    total_size_before = 0
    total_size_after = 0
    optimized_count = 0
    error_count = 0
    
    print("\nدر حال پردازش...")
    print("-" * 50)
    
    for index, anomaly in enumerate(anomalies_with_images, 1):
        try:
            if not anomaly.image:
                continue
            
            # دریافت مسیر فایل
            image_path = anomaly.image.path
            
            # بررسی وجود فایل
            if not os.path.exists(image_path):
                print(f"[{index}/{total_count}] فایل وجود ندارد: {anomaly.id}")
                error_count += 1
                continue
            
            # دریافت حجم قبل از بهینه‌سازی
            size_before = os.path.getsize(image_path)
            total_size_before += size_before
            
            # فشرده‌سازی تصویر
            with open(image_path, 'rb') as f:
                compressed_image = compress_image(File(f), max_size_mb=1, quality=85)
            
            # بررسی اینکه آیا فشرده‌سازی انجام شده
            if compressed_image and hasattr(compressed_image, 'size'):
                # ذخیره فایل فشرده شده
                anomaly.image.save(
                    anomaly.image.name.split('/')[-1],
                    compressed_image,
                    save=False
                )
                anomaly.save(update_fields=['image'])
                
                # دریافت حجم بعد از بهینه‌سازی
                size_after = os.path.getsize(anomaly.image.path)
                total_size_after += size_after
                
                # محاسبه درصد کاهش
                reduction_percent = ((size_before - size_after) / size_before) * 100 if size_before > 0 else 0
                
                if size_after < size_before:
                    optimized_count += 1
                    print(f"[{index}/{total_count}] آنومالی #{anomaly.id}: "
                          f"{size_before/1024/1024:.2f}MB → {size_after/1024/1024:.2f}MB "
                          f"({reduction_percent:.1f}% کاهش)")
                else:
                    total_size_after += (size_before - size_after)  # اصلاح محاسبه
                    print(f"[{index}/{total_count}] آنومالی #{anomaly.id}: نیازی به فشرده‌سازی نبود")
            else:
                total_size_after += size_before
                print(f"[{index}/{total_count}] آنومالی #{anomaly.id}: نیازی به فشرده‌سازی نبود")
                
        except Exception as e:
            error_count += 1
            print(f"[{index}/{total_count}] خطا در پردازش آنومالی #{anomaly.id}: {str(e)}")
            continue
    
    print("-" * 50)
    print("\n" + "=" * 50)
    print("خلاصه نتایج:")
    print("=" * 50)
    print(f"تعداد کل: {total_count}")
    print(f"بهینه‌سازی شده: {optimized_count}")
    print(f"خطاها: {error_count}")
    print(f"حجم کل قبل: {total_size_before/1024/1024/1024:.2f} GB")
    print(f"حجم کل بعد: {total_size_after/1024/1024/1024:.2f} GB")
    
    if total_size_before > 0:
        total_reduction = total_size_before - total_size_after
        total_reduction_percent = (total_reduction / total_size_before) * 100
        print(f"کاهش کل: {total_reduction/1024/1024/1024:.2f} GB ({total_reduction_percent:.1f}%)")
    
    print("=" * 50)


if __name__ == '__main__':
    optimize_existing_images()
