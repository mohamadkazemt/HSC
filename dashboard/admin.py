"""Django Admin configuration for Notification and SMS management."""

from django.contrib import admin

from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.db.models import Count, Q
from django.http import HttpResponse
import csv
from datetime import timedelta

from .models import Notification, UserActivity
from .models_sms import SMSLog, SMSTemplate


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_link', 'title_display', 'notification_type_badge', 'is_read', 'created_at_display', 'actions_column']
    list_filter = ['notification_type', 'is_read', 'created_at', 'user__is_staff']
    search_fields = ['title', 'message', 'user__username', 'user__first_name', 'user__last_name']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'read_at']
    list_per_page = 50
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('user', 'title', 'message', 'notification_type', 'url')
        }),
        ('وضعیت', {
            'fields': ('is_read', 'read_at', 'created_at')
        }),
        ('ارتباطات', {
            'fields': ('meeting',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread', 'delete_selected_notifications', 'export_to_csv']
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name() or obj.user.username)
    user_link.short_description = 'کاربر'
    
    def title_display(self, obj):
        return obj.title[:50] + '...' if obj.title and len(obj.title) > 50 else obj.title
    title_display.short_description = 'عنوان'
    
    def notification_type_badge(self, obj):
        colors = {
            'info': '#0dcaf0',
            'success': '#198754',
            'warning': '#ffc107',
            'error': '#dc3545',
            'meeting': '#0d6efd',
        }
        color = colors.get(obj.notification_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_notification_type_display()
        )
    notification_type_badge.short_description = 'نوع'
    
    def created_at_display(self, obj):
        now = timezone.now()
        diff = now - obj.created_at
        if diff < timedelta(minutes=1):
            return format_html('<span style="color: #28a745;">همین الان</span>')
        elif diff < timedelta(hours=1):
            return format_html('<span style="color: #28a745;">{} دقیقه پیش</span>', int(diff.seconds / 60))
        elif diff < timedelta(days=1):
            return format_html('<span style="color: #ffc107;">{} ساعت پیش</span>', int(diff.seconds / 3600))
        else:
            return format_html('<span>{} روز پیش</span>', diff.days)
    created_at_display.short_description = 'زمان ایجاد'
    
    def actions_column(self, obj):
        if obj.url:
            return format_html('<a href="{}" target="_blank" style="color: #0d6efd;">مشاهده</a>', obj.url)
        return '-'
    actions_column.short_description = 'عملیات'
    
    def mark_as_read(self, request, queryset):
        count = queryset.filter(is_read=False).update(is_read=True, read_at=timezone.now())
        self.message_user(request, f'{count} اعلان به عنوان خوانده‌شده علامت‌گذاری شد.')
    mark_as_read.short_description = 'علامت‌گذاری به عنوان خوانده‌شده'
    
    def mark_as_unread(self, request, queryset):
        count = queryset.filter(is_read=True).update(is_read=False, read_at=None)
        self.message_user(request, f'{count} اعلان به عنوان خوانده‌نشده علامت‌گذاری شد.')
    mark_as_unread.short_description = 'علامت‌گذاری به عنوان خوانده‌نشده'
    
    def delete_selected_notifications(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} اعلان حذف شد.')
    delete_selected_notifications.short_description = 'حذف اعلان‌های انتخاب‌شده'
    
    def export_to_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="notifications.csv"'
        response.write('\ufeff')  # UTF-8 BOM
        
        writer = csv.writer(response)
        writer.writerow(['شناسه', 'کاربر', 'عنوان', 'پیام', 'نوع', 'خوانده‌شده', 'تاریخ ایجاد'])
        
        for notif in queryset:
            writer.writerow([
                notif.id,
                notif.user.get_full_name() or notif.user.username,
                notif.title,
                notif.message,
                notif.get_notification_type_display(),
                'بله' if notif.is_read else 'خیر',
                notif.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
    export_to_csv.short_description = 'خروجی CSV'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'meeting')


@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'mobile_number', 'template_id', 'user_link', 'status_badge', 'track_id_display', 'created_at_display', 'cost_display']
    list_filter = ['status', 'template_id', 'created_at', 'user__is_staff']
    search_fields = ['mobile_number', 'track_id', 'user__username', 'error_message']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'sent_at', 'delivered_at', 'response_data']
    list_per_page = 50
    
    fieldsets = (
        ('اطلاعات ارسال', {
            'fields': ('mobile_number', 'template_id', 'parameters', 'user')
        }),
        ('وضعیت', {
            'fields': ('status', 'track_id', 'error_message')
        }),
        ('زمان‌ها', {
            'fields': ('created_at', 'sent_at', 'delivered_at')
        }),
        ('پاسخ سرویس', {
            'fields': ('response_data',),
            'classes': ('collapse',)
        }),
        ('متادیتا', {
            'fields': ('estimated_cost', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['retry_failed_sms', 'export_to_csv', 'calculate_total_cost']
    
    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name() or obj.user.username)
        return '-'
    user_link.short_description = 'کاربر'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#6c757d',
            'sent': '#0dcaf0',
            'delivered': '#198754',
            'failed': '#dc3545',
            'rate_limited': '#ffc107',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'وضعیت'
    
    def track_id_display(self, obj):
        if obj.track_id:
            return format_html('<code style="background: #f5f5f5; padding: 2px 5px;">{}</code>', obj.track_id)
        return '-'
    track_id_display.short_description = 'شناسه رهگیری'
    
    def created_at_display(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
    created_at_display.short_description = 'تاریخ ایجاد'
    
    def cost_display(self, obj):
        if obj.estimated_cost > 0:
            return format_html('{:,} ریال', int(obj.estimated_cost))
        return '-'
    cost_display.short_description = 'هزینه'
    
    def retry_failed_sms(self, request, queryset):
        from core.sms_service import send_template_sms
        failed = queryset.filter(status='failed')
        retry_count = 0
        
        for sms in failed:
            ok = send_template_sms(
                sms.mobile_number,
                sms.template_id,
                sms.parameters,
                user_id=sms.user.id if sms.user else None
            )
            if ok:
                retry_count += 1
        
        self.message_user(request, f'{retry_count} پیامک با موفقیت مجدداً ارسال شد.')
    retry_failed_sms.short_description = 'ارسال مجدد پیامک‌های ناموفق'
    
    def export_to_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="sms_logs.csv"'
        response.write('\ufeff')
        
        writer = csv.writer(response)
        writer.writerow(['شناسه', 'شماره موبایل', 'قالب', 'کاربر', 'وضعیت', 'شناسه رهگیری', 'تاریخ ایجاد', 'هزینه'])
        
        for sms in queryset:
            writer.writerow([
                sms.id,
                sms.mobile_number,
                sms.template_id,
                sms.user.get_full_name() if sms.user else '-',
                sms.get_status_display(),
                sms.track_id or '-',
                sms.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                int(sms.estimated_cost) if sms.estimated_cost else 0
            ])
        
        return response
    export_to_csv.short_description = 'خروجی CSV'
    
    def calculate_total_cost(self, request, queryset):
        total = sum(log.estimated_cost for log in queryset if log.estimated_cost)
        count = queryset.count()
        self.message_user(request, f'مجموع هزینه {count} پیامک: {total:,} ریال')
    calculate_total_cost.short_description = 'محاسبه مجموع هزینه'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')


@admin.register(SMSTemplate)
class SMSTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_id', 'is_active', 'usage_count', 'created_at', 'actions_column']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description', 'template_text']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'template_id', 'description', 'is_active')
        }),
        ('محتوا', {
            'fields': ('template_text', 'parameters')
        }),
        ('آمار', {
            'fields': ('usage_count', 'created_at', 'updated_at')
        }),
    )
    
    actions = ['activate_templates', 'deactivate_templates', 'reset_usage_count']
    
    def actions_column(self, obj):
        return format_html('<a href="#" onclick="previewTemplate({})">پیش‌نمایش</a>', obj.id)
    actions_column.short_description = 'عملیات'
    
    def activate_templates(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} قالب فعال شد.')
    activate_templates.short_description = 'فعال‌سازی قالب‌های انتخابی'
    
    def deactivate_templates(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} قالب غیرفعال شد.')
    deactivate_templates.short_description = 'غیرفعال‌سازی قالب‌های انتخابی'
    
    def reset_usage_count(self, request, queryset):
        count = queryset.update(usage_count=0)
        self.message_user(request, f'شمارنده استفاده {count} قالب بازنشانی شد.')
    reset_usage_count.short_description = 'بازنشانی شمارنده استفاده'


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_link', 'activity_type', 'description_short', 'created_at_display', 'ip_address']
    list_filter = ['activity_type', 'created_at', 'user__is_staff']
    search_fields = ['user__username', 'description', 'related_model', 'ip_address']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']
    list_per_page = 100
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name() or obj.user.username)
    user_link.short_description = 'کاربر'
    
    def description_short(self, obj):
        return obj.description[:60] + '...' if len(obj.description) > 60 else obj.description
    description_short.short_description = 'توضیحات'
    
    def created_at_display(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
    created_at_display.short_description = 'تاریخ'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')


# Customize admin site header and title
admin.site.site_header = 'پنل مدیریت HSC'
admin.site.site_title = 'مدیریت سیستم'
admin.site.index_title = 'داشبورد مدیریتی'
