"""
Django Management Command برای بهینه‌سازی تصاویر آنومالی

نحوه استفاده:
    python manage.py optimize_anomaly_images
    python manage.py optimize_anomaly_images --dry-run  # فقط نمایش بدون تغییر
    python manage.py optimize_anomaly_images --max-size 0.5  # تنظیم حداکثر حجم به 0.5 مگابایت
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.files.base import File
from anomalis.models import Anomaly
from anomalis.utils import compress_image
import os


class Command(BaseCommand):
    help = 'فشرده‌سازی و بهینه‌سازی تصاویر موجود در آنومالی‌ها'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='نمایش آنچه انجام خواهد شد بدون اعمال تغییرات',
        )
        parser.add_argument(
            '--max-size',
            type=float,
            default=1.0,
            help='حداکثر حجم فایل به مگابایت (پیش‌فرض: 1.0)',
        )
        parser.add_argument(
            '--quality',
            type=int,
            default=85,
            help='کیفیت فشرده‌سازی (1-100، پیش‌فرض: 85)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='محدود کردن تعداد تصاویر پردازش شده',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        max_size = options['max_size']
        quality = options['quality']
        limit = options['limit']

        # بررسی اعتبار پارامترها
        if max_size <= 0:
            raise CommandError('حداکثر حجم باید بزرگتر از 0 باشد')
        
        if quality < 1 or quality > 100:
            raise CommandError('کیفیت باید بین 1 تا 100 باشد')

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('شروع بهینه‌سازی تصاویر آنومالی'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  حالت DRY-RUN: هیچ تغییری اعمال نخواهد شد\n'))

        # دریافت آنومالی‌ها با تصویر
        anomalies = Anomaly.objects.exclude(image='').exclude(image__isnull=True)
        
        if limit:
            anomalies = anomalies[:limit]
            
        total_count = anomalies.count()

        if total_count == 0:
            self.stdout.write(self.style.WARNING('هیچ تصویری برای بهینه‌سازی یافت نشد.'))
            return

        self.stdout.write(f'\n📊 تعداد کل آنومالی‌ها با تصویر: {total_count}')
        self.stdout.write(f'⚙️  حداکثر حجم: {max_size} MB')
        self.stdout.write(f'🎨 کیفیت: {quality}%\n')

        # آمارها
        total_size_before = 0
        total_size_after = 0
        optimized_count = 0
        skipped_count = 0
        error_count = 0

        self.stdout.write(self.style.SUCCESS('\n' + '-' * 70))
        self.stdout.write('شروع پردازش...\n')

        for index, anomaly in enumerate(anomalies, 1):
            try:
                if not anomaly.image:
                    continue

                image_path = anomaly.image.path

                # بررسی وجود فایل
                if not os.path.exists(image_path):
                    self.stdout.write(
                        self.style.ERROR(f'[{index}/{total_count}] ❌ فایل وجود ندارد: آنومالی #{anomaly.id}')
                    )
                    error_count += 1
                    continue

                # حجم قبل از بهینه‌سازی
                size_before = os.path.getsize(image_path)
                size_before_mb = size_before / 1024 / 1024
                total_size_before += size_before

                # اگر فایل کوچکتر از حد مجاز است
                if size_before_mb <= max_size:
                    self.stdout.write(
                        f'[{index}/{total_count}] ⏭️  آنومالی #{anomaly.id}: '
                        f'{size_before_mb:.2f}MB - نیازی به بهینه‌سازی ندارد'
                    )
                    total_size_after += size_before
                    skipped_count += 1
                    continue

                # فشرده‌سازی
                if not dry_run:
                    with open(image_path, 'rb') as f:
                        compressed_image = compress_image(
                            File(f),
                            max_size_mb=max_size,
                            quality=quality
                        )

                    if compressed_image and hasattr(compressed_image, 'size'):
                        # ذخیره فایل فشرده شده
                        original_name = os.path.basename(anomaly.image.name)
                        anomaly.image.save(
                            original_name,
                            compressed_image,
                            save=False
                        )
                        anomaly.save(update_fields=['image'])

                        # حجم بعد از بهینه‌سازی
                        size_after = os.path.getsize(anomaly.image.path)
                        size_after_mb = size_after / 1024 / 1024
                        total_size_after += size_after

                        # محاسبه درصد کاهش
                        if size_after < size_before:
                            reduction_percent = ((size_before - size_after) / size_before) * 100
                            saved_mb = (size_before - size_after) / 1024 / 1024

                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'[{index}/{total_count}] ✅ آنومالی #{anomaly.id}: '
                                    f'{size_before_mb:.2f}MB → {size_after_mb:.2f}MB '
                                    f'(↓{reduction_percent:.1f}% / {saved_mb:.2f}MB)'
                                )
                            )
                            optimized_count += 1
                        else:
                            self.stdout.write(
                                f'[{index}/{total_count}] ⏭️  آنومالی #{anomaly.id}: '
                                f'بدون تغییر ({size_after_mb:.2f}MB)'
                            )
                            skipped_count += 1
                    else:
                        total_size_after += size_before
                        skipped_count += 1
                else:
                    # حالت dry-run
                    self.stdout.write(
                        self.style.WARNING(
                            f'[{index}/{total_count}] 🔍 آنومالی #{anomaly.id}: '
                            f'{size_before_mb:.2f}MB - قابل بهینه‌سازی'
                        )
                    )
                    optimized_count += 1

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'[{index}/{total_count}] ❌ خطا در پردازش آنومالی #{anomaly.id}: {str(e)}'
                    )
                )
                continue

        # خلاصه نتایج
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('📈 خلاصه نتایج:'))
        self.stdout.write('=' * 70)
        self.stdout.write(f'📊 تعداد کل: {total_count}')
        self.stdout.write(self.style.SUCCESS(f'✅ بهینه‌سازی شده: {optimized_count}'))
        self.stdout.write(f'⏭️  رد شده (نیاز نبود): {skipped_count}')
        
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'❌ خطاها: {error_count}'))

        if not dry_run:
            total_size_before_gb = total_size_before / 1024 / 1024 / 1024
            total_size_after_gb = total_size_after / 1024 / 1024 / 1024
            
            self.stdout.write(f'\n💾 حجم کل قبل: {total_size_before_gb:.3f} GB')
            self.stdout.write(f'💾 حجم کل بعد: {total_size_after_gb:.3f} GB')

            if total_size_before > 0:
                total_reduction = total_size_before - total_size_after
                total_reduction_gb = total_reduction / 1024 / 1024 / 1024
                total_reduction_percent = (total_reduction / total_size_before) * 100
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'💰 کاهش کل: {total_reduction_gb:.3f} GB '
                        f'(↓{total_reduction_percent:.1f}%)'
                    )
                )

        self.stdout.write('=' * 70)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    '\n💡 برای اعمال تغییرات، دستور را بدون --dry-run اجرا کنید'
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS('\n✨ بهینه‌سازی با موفقیت انجام شد!'))
