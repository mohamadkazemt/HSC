import os
import glob
import json
from datetime import datetime, timedelta
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import re


def custom_403_handler(request, exception):
    """
    هندلر سفارشی برای ارور 403
    """
    return render(request, 'core/403.html', status=403)


@staff_member_required
def log_dashboard(request):
    """داشبورد اصلی لاگ‌ها"""
    logs_dir = os.path.join(settings.BASE_DIR, 'logs')
    
    # اگر پوشه logs وجود ندارد، ایجاد کن
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # آمار کلی فایل‌ها
    log_files = []
    total_size = 0
    
    for log_file in glob.glob(os.path.join(logs_dir, '*.log')):
        if os.path.isfile(log_file):
            size = os.path.getsize(log_file)
            total_size += size
            mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
            
            log_files.append({
                'name': os.path.basename(log_file),
                'path': log_file,
                'size': size,
                'size_human': format_size(size),
                'modified': mtime,
                'lines': count_lines(log_file)
            })
    
    # مرتب‌سازی بر اساس آخرین تغییرات
    log_files.sort(key=lambda x: x['modified'], reverse=True)
    
    context = {
        'log_files': log_files,
        'total_files': len(log_files),
        'total_size': format_size(total_size),
        'logs_dir': logs_dir
    }
    
    return render(request, 'core/log_dashboard.html', context)


@staff_member_required 
def view_log(request, log_name):
    """نمایش محتویات یک فایل لاگ"""
    logs_dir = os.path.join(settings.BASE_DIR, 'logs')
    log_path = os.path.join(logs_dir, log_name)
    
    # بررسی امنیت - فقط فایل‌های .log مجاز
    if not log_name.endswith('.log') or not os.path.exists(log_path):
        return render(request, 'core/log_error.html', {
            'error': 'فایل مورد نظر یافت نشد یا مجاز نیست.'
        })
    
    # پارامترهای فیلتر و صفحه‌بندی
    search_term = request.GET.get('search', '')
    level_filter = request.GET.get('level', '')
    date_filter = request.GET.get('date', '')
    page_num = request.GET.get('page', 1)
    lines_per_page = int(request.GET.get('per_page', 100))
    
    # خواندن فایل
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        return render(request, 'core/log_error.html', {
            'error': f'خطا در خواندن فایل: {str(e)}'
        })
    
    # پردازش خطوط و استخراج اطلاعات
    processed_lines = []
    for i, line in enumerate(lines):
        line = line.rstrip('\n\r')
        if not line:
            continue
            
        log_entry = parse_log_line(line, i + 1)
        
        # اعمال فیلترها
        if search_term and search_term.lower() not in line.lower():
            continue
        if level_filter and log_entry['level'] != level_filter:
            continue
        if date_filter and not log_entry['timestamp'].startswith(date_filter):
            continue
            
        processed_lines.append(log_entry)
    
    # صفحه‌بندی
    paginator = Paginator(processed_lines, lines_per_page)
    page_obj = paginator.get_page(page_num)
    
    # آمار levels
    level_stats = {}
    for line in processed_lines:
        level = line['level']
        level_stats[level] = level_stats.get(level, 0) + 1
    
    context = {
        'log_name': log_name,
        'log_path': log_path,
        'page_obj': page_obj,
        'total_lines': len(processed_lines),
        'original_lines': len(lines),
        'level_stats': level_stats,
        'search_term': search_term,
        'level_filter': level_filter,
        'date_filter': date_filter,
        'lines_per_page': lines_per_page,
    }
    
    return render(request, 'core/view_log.html', context)


@staff_member_required
def download_log(request, log_name):
    """دانلود فایل لاگ"""
    logs_dir = os.path.join(settings.BASE_DIR, 'logs')
    log_path = os.path.join(logs_dir, log_name)
    
    if not log_name.endswith('.log') or not os.path.exists(log_path):
        return HttpResponse('فایل یافت نشد', status=404)
    
    try:
        with open(log_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='text/plain')
            response['Content-Disposition'] = f'attachment; filename="{log_name}"'
            return response
    except Exception as e:
        return HttpResponse(f'خطا: {str(e)}', status=500)


@staff_member_required
@require_http_methods(["POST"])
@csrf_exempt
def clear_log(request, log_name):
    """پاک کردن محتویات فایل لاگ"""
    logs_dir = os.path.join(settings.BASE_DIR, 'logs')
    log_path = os.path.join(logs_dir, log_name)
    
    if not log_name.endswith('.log') or not os.path.exists(log_path):
        return JsonResponse({'error': 'فایل یافت نشد'}, status=404)
    
    try:
        # بک‌آپ گیری قبل از پاک کردن
        backup_name = f"{log_name}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = os.path.join(logs_dir, backup_name)
        
        import shutil
        shutil.copy2(log_path, backup_path)
        
        # پاک کردن فایل اصلی
        open(log_path, 'w').close()
        
        return JsonResponse({
            'success': True,
            'message': f'فایل {log_name} پاک شد. بک‌آپ در {backup_name} ذخیره شد.'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
def log_stats_api(request):
    """API برای آمار لاگ‌ها (برای نمودارها)"""
    logs_dir = os.path.join(settings.BASE_DIR, 'logs')
    
    # آمار کلی
    stats = {
        'total_files': 0,
        'total_size': 0,
        'levels': {'DEBUG': 0, 'INFO': 0, 'WARNING': 0, 'ERROR': 0, 'CRITICAL': 0},
        'hourly': {},
        'daily': {}
    }
    
    for log_file in glob.glob(os.path.join(logs_dir, '*.log')):
        if os.path.isfile(log_file):
            stats['total_files'] += 1
            stats['total_size'] += os.path.getsize(log_file)
            
            # تحلیل محتوا (فقط 1000 خط آخر برای سرعت)
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[-1000:]
                    
                for line in lines:
                    log_entry = parse_log_line(line.strip())
                    
                    # آمار سطح لاگ
                    level = log_entry['level']
                    if level in stats['levels']:
                        stats['levels'][level] += 1
                    
                    # آمار ساعتی و روزانه
                    try:
                        dt = datetime.strptime(log_entry['timestamp'][:19], '%Y-%m-%d %H:%M:%S')
                        hour_key = dt.strftime('%H:00')
                        day_key = dt.strftime('%Y-%m-%d')
                        
                        stats['hourly'][hour_key] = stats['hourly'].get(hour_key, 0) + 1
                        stats['daily'][day_key] = stats['daily'].get(day_key, 0) + 1
                    except:
                        pass
                        
            except:
                continue
    
    return JsonResponse(stats)


def parse_log_line(line, line_number=None):
    """پارس کردن یک خط لاگ"""
    # پترن‌های مختلف لاگ Django
    patterns = [
        r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] (\w+) ([^|]+) \| (.+)',
        r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] (\w+) \| (.+)',
        r'(\w+) (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[^|]+) \| (.+)'
    ]
    
    for pattern in patterns:
        match = re.match(pattern, line)
        if match:
            if len(match.groups()) == 4:
                timestamp, level, module, message = match.groups()
            elif len(match.groups()) == 3:
                if match.group(1).replace('-', '').replace(' ', '').replace(':', '').isdigit():
                    timestamp, level, message = match.groups()
                    module = ''
                else:
                    level, timestamp, message = match.groups()
                    module = ''
            
            return {
                'line_number': line_number,
                'timestamp': timestamp.strip(),
                'level': level.strip(),
                'module': module.strip(),
                'message': message.strip(),
                'raw': line,
                'css_class': get_level_css_class(level.strip())
            }
    
    # اگر پترن پیدا نشد، خط را به صورت ساده برگردان
    return {
        'line_number': line_number,
        'timestamp': '',
        'level': 'UNKNOWN',
        'module': '',
        'message': line,
        'raw': line,
        'css_class': 'text-secondary'
    }


def get_level_css_class(level):
    """برگرداندن کلاس CSS بر اساس سطح لاگ"""
    level_colors = {
        'DEBUG': 'text-muted',
        'INFO': 'text-info',
        'WARNING': 'text-warning',
        'ERROR': 'text-danger',
        'CRITICAL': 'text-danger fw-bold',
        'UNKNOWN': 'text-secondary'
    }
    return level_colors.get(level.upper(), 'text-secondary')


def count_lines(file_path):
    """شمارش خطوط فایل"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)
    except:
        return 0


def format_size(size_bytes):
    """فرمت کردن اندازه فایل"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"
