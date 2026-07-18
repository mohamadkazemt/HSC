from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
import os


class ModuleSetting(models.Model):
    """Global on/off switch for a business application."""

    module_key = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="ماژول",
    )
    is_active = models.BooleanField(default=True, verbose_name="فعال است")
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="modified_modules",
        verbose_name="آخرین تغییر توسط",
    )
    modified_at = models.DateTimeField(auto_now=True, verbose_name="آخرین تغییر")

    def __str__(self):
        from .module_registry import get_module_title

        return get_module_title(self.module_key)

    def delete(self, *args, **kwargs):
        # Module switches are configuration records and must not disappear.
        return None

    class Meta:
        verbose_name = "ماژول سایت"
        verbose_name_plural = "فعال/غیرفعال‌سازی ماژول‌ها"

class SiteSettings(models.Model):
    site_name = models.CharField(max_length=255, default='My Site')
    site_favicon = models.ImageField(upload_to='logos/', blank=True, null=True)
    company_logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    seo_description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        if not self.pk and SiteSettings.objects.exists():
            raise ValidationError('There can be only one SiteSettings instance')
        return super(SiteSettings, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"
