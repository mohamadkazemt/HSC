# hse_docs/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import TopicCategory, Document
import qrcode
from io import BytesIO
import base64
import jdatetime
from persiantools import digits as persian_digits


@admin.register(TopicCategory)
class TopicCategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'icon_display', 'document_count', 'created_at_jalali']
    list_filter = ['created_at']
    search_fields = ['title', 'slug']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at', 'created_at_jalali', 'updated_at_jalali']

    def icon_display(self, obj):
        if obj.icon:
            return format_html('<i class="{}"></i> {}', obj.icon, obj.icon)
        return '-'
    icon_display.short_description = "آیکون"

    def document_count(self, obj):
        count = obj.documents.filter(is_active=True).count()
        return count
    document_count.short_description = "تعداد اسناد"

    def created_at_jalali(self, obj):
        if obj.created_at:
            j = jdatetime.datetime.fromgregorian(datetime=obj.created_at)
            result = j.strftime('%Y/%m/%d')
            return persian_digits.en_to_fa(result)
        return '-'
    created_at_jalali.short_description = 'تاریخ ایجاد (شمسی)'

    def updated_at_jalali(self, obj):
        if obj.updated_at:
            j = jdatetime.datetime.fromgregorian(datetime=obj.updated_at)
            result = j.strftime('%Y/%m/%d')
            return persian_digits.en_to_fa(result)
        return '-'
    updated_at_jalali.short_description = 'تاریخ بروزرسانی (شمسی)'


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'topic_category',
        'section',
        'unit_group',
        'version',
        'file_link',
        'uploaded_at_jalali',
        'is_active'
    ]
    list_filter = [
        'topic_category',
        'section',
        'unit_group',
        'is_active',
        'uploaded_at'
    ]
    search_fields = ['title', 'description']
    readonly_fields = ['uploaded_at', 'uploaded_by', 'uploaded_at_jalali', 'qr_code_display']
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('title', 'description', 'file', 'version', 'is_active')
        }),
        ('دسته‌بندی و موقعیت', {
            'fields': ('topic_category', 'section', 'unit_group'),
            'description': 'هر سند باید یک دسته‌بندی موضوع داشته باشد. بخش و گروه اختیاری هستند.'
        }),
        ('اطلاعات سیستم', {
            'fields': ('uploaded_at', 'uploaded_at_jalali', 'uploaded_by', 'qr_code_display'),
            'classes': ('collapse',)
        }),
    )

    def file_link(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">📄 دانلود</a>',
                obj.file.url
            )
        return '-'
    file_link.short_description = "فایل"

    def qr_code_display(self, obj):
        """Generate QR code for this document"""
        if not obj.pk:
            return "پس از ذخیره، QR کد نمایش داده می‌شود"
        
        # Generate QR code URL
        from django.conf import settings
        qr_url = reverse('hse_docs:document_detail', kwargs={'pk': obj.pk})
        # Note: In production, use request.build_absolute_uri() in views
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        full_url = f"{base_url}{qr_url}"
        
        try:
            # Create QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(full_url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            # Convert to base64 for display
            img_str = base64.b64encode(buffer.read()).decode()
            return format_html(
                '<img src="data:image/png;base64,{}" style="max-width: 200px;" /><br><small class="text-gray-500">{}</small>',
                img_str,
                full_url
            )
        except Exception as e:
            return format_html('<span class="text-red-500">خطا در تولید QR: {}</span>', str(e))
    qr_code_display.short_description = "QR کد سند"

    def uploaded_at_jalali(self, obj):
        if obj.uploaded_at:
            j = jdatetime.datetime.fromgregorian(datetime=obj.uploaded_at)
            result = j.strftime('%Y/%m/%d %H:%M')
            return persian_digits.en_to_fa(result)
        return '-'
    uploaded_at_jalali.short_description = 'تاریخ بارگذاری (شمسی)'

    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


