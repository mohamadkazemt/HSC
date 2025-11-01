from django.db import models
from django.core.exceptions import ValidationError
import os

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
