import os
import glob
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = 'Manage log files: cleanup old logs, archive, and report statistics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up old log files'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to keep logs (default: 30)'
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Show log statistics'
        )
        parser.add_argument(
            '--archive',
            action='store_true',
            help='Archive old logs'
        )

    def handle(self, *args, **options):
        logs_dir = os.path.join(settings.BASE_DIR, 'logs')
        
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
            self.stdout.write(
                self.style.SUCCESS(f'Created logs directory: {logs_dir}')
            )

        if options['cleanup']:
            self.cleanup_logs(logs_dir, options['days'])
        
        if options['stats']:
            self.show_stats(logs_dir)
        
        if options['archive']:
            self.archive_logs(logs_dir)

    def cleanup_logs(self, logs_dir, days):
        """حذف فایل‌های قدیمی"""
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0
        deleted_size = 0
        
        # پترن فایل‌های log
        patterns = ['*.log.*', '*.log.????-??-??']
        
        for pattern in patterns:
            for log_file in glob.glob(os.path.join(logs_dir, pattern)):
                try:
                    file_stat = os.stat(log_file)
                    file_date = datetime.fromtimestamp(file_stat.st_mtime)
                    
                    if file_date < cutoff_date:
                        file_size = file_stat.st_size
                        os.remove(log_file)
                        deleted_count += 1
                        deleted_size += file_size
                        
                        self.stdout.write(f'Deleted: {log_file}')
                        
                except OSError as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error deleting {log_file}: {e}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Cleanup complete: {deleted_count} files deleted, '
                f'{self.format_size(deleted_size)} freed'
            )
        )

    def show_stats(self, logs_dir):
        """نمایش آمار لاگ‌ها"""
        self.stdout.write(self.style.SUCCESS('\n=== Log Statistics ==='))
        
        total_size = 0
        file_count = 0
        
        # فایل‌های log فعال
        for log_file in glob.glob(os.path.join(logs_dir, '*.log')):
            if os.path.isfile(log_file):
                size = os.path.getsize(log_file)
                total_size += size
                file_count += 1
                
                # آخرین تغییرات
                mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
                
                self.stdout.write(
                    f'{os.path.basename(log_file):<25} | '
                    f'{self.format_size(size):<10} | '
                    f'Last modified: {mtime.strftime("%Y-%m-%d %H:%M")}'
                )
        
        # فایل‌های آرشیو
        archive_count = 0
        archive_size = 0
        
        patterns = ['*.log.*', '*.log.????-??-??']
        for pattern in patterns:
            for archive_file in glob.glob(os.path.join(logs_dir, pattern)):
                if os.path.isfile(archive_file):
                    archive_size += os.path.getsize(archive_file)
                    archive_count += 1
        
        self.stdout.write('\n=== Summary ===')
        self.stdout.write(f'Active log files: {file_count} ({self.format_size(total_size)})')
        self.stdout.write(f'Archive files: {archive_count} ({self.format_size(archive_size)})')
        self.stdout.write(f'Total: {file_count + archive_count} files ({self.format_size(total_size + archive_size)})')

    def archive_logs(self, logs_dir):
        """آرشیو کردن لاگ‌های قدیمی"""
        import gzip
        import shutil
        
        archived_count = 0
        
        # فایل‌های log بزرگ (بیش از 10MB)
        for log_file in glob.glob(os.path.join(logs_dir, '*.log')):
            if os.path.getsize(log_file) > 10 * 1024 * 1024:  # 10MB
                try:
                    # نام فایل آرشیو
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    base_name = os.path.basename(log_file)
                    archive_name = f"{base_name}.{timestamp}.gz"
                    archive_path = os.path.join(logs_dir, archive_name)
                    
                    # فشرده‌سازی
                    with open(log_file, 'rb') as f_in:
                        with gzip.open(archive_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    # پاک کردن فایل اصلی
                    os.remove(log_file)
                    
                    # ایجاد فایل جدید
                    open(log_file, 'w').close()
                    
                    archived_count += 1
                    self.stdout.write(f'Archived: {base_name} -> {archive_name}')
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error archiving {log_file}: {e}')
                    )
        
        if archived_count == 0:
            self.stdout.write('No files needed archiving.')
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Archived {archived_count} log files')
            )

    def format_size(self, size_bytes):
        """فرمت کردن اندازه فایل"""
        if size_bytes == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f}{size_names[i]}"