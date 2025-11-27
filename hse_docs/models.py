# hse_docs/models.py
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from accounts.models import Section, UnitGroup


class TopicCategory(models.Model):
    """Represents the 'Type' of document (What it is)"""
    title = models.CharField(max_length=100, verbose_name="عنوان")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="نامک")
    icon = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="نام آیکون Font Awesome (مثال: fa-file-alt)",
        verbose_name="آیکون"
    )
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")

    class Meta:
        verbose_name = "دسته‌بندی موضوع"
        verbose_name_plural = "دسته‌بندی‌های موضوع"
        ordering = ['title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


def document_upload_path(instance, filename):
    """Generate upload path for documents"""
    import uuid
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    return f'hse_docs/{instance.topic_category.slug}/{filename}'


class Document(models.Model):
    """HSE Document with matrix relationship: TopicCategory (required) + Section/UnitGroup (optional)"""
    title = models.CharField(max_length=200, verbose_name="عنوان")
    file = models.FileField(upload_to=document_upload_path, verbose_name="فایل")
    version = models.CharField(max_length=20, default="1.0", verbose_name="نسخه")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ بارگذاری")
    uploaded_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="بارگذاری شده توسط"
    )
    
    # Matrix Relationships
    topic_category = models.ForeignKey(
        TopicCategory,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name="دسته‌بندی موضوع"
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        verbose_name="بخش"
    )
    unit_group = models.ForeignKey(
        UnitGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        verbose_name="گروه"
    )
    
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    
    class Meta:
        verbose_name = "سند"
        verbose_name_plural = "اسناد"
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['topic_category', 'section', 'unit_group']),
            models.Index(fields=['is_active', '-uploaded_at']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('hse_docs:document_detail', kwargs={'pk': self.pk})

    def get_file_extension(self):
        """Get file extension for icon display"""
        if self.file:
            return self.file.name.split('.')[-1].lower()
        return ''

    def get_file_size(self):
        """Get human-readable file size"""
        try:
            size = self.file.size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        except (ValueError, AttributeError):
            return "نامشخص"
