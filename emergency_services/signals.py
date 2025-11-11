from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.models import User, Group

from dashboard.models import Notification
from .models import Medicine, MedicineUsage


@receiver(post_save, sender=Medicine)
def handle_medicine_notifications(sender, instance, created, **kwargs):
    """ایجاد هشدار برای داروهای نزدیک به حد بحرانی یا منقضی شده"""
    try:
        # دریافت گروه‌های مدیر HSE و مدیر اورژانس
        hse_group = Group.objects.filter(name='مدیر HSE').first()
        emergency_group = Group.objects.filter(name='مدیر اورژانس').first()
        
        # دریافت کاربران این گروه‌ها
        managers = []
        if hse_group:
            managers.extend(User.objects.filter(groups=hse_group))
        if emergency_group:
            managers.extend(User.objects.filter(groups=emergency_group))
        
        # اگر هیچ مدیری پیدا نشد، از همه کاربران ادمین استفاده می‌کنیم
        if not managers:
            managers = User.objects.filter(is_superuser=True)
        
        if instance.is_critical() and instance.is_active:
            # هشدار برای موجودی کم
            for manager in managers:
                Notification.objects.create(
                    user=manager,
                    title="هشدار موجودی دارو",
                    message=f"موجودی داروی {instance.name} به حد بحرانی ({instance.quantity} از {instance.critical_threshold}) رسیده است.",
                    notification_type="warning",
                    is_read=False
                )
        
        if instance.is_expired() and instance.is_active:
            # غیرفعال کردن خودکار دارو منقضی شده
            with transaction.atomic():
                Medicine.objects.filter(pk=instance.pk).update(is_active=False)
            
            # هشدار برای منقضی شدن
            for manager in managers:
                Notification.objects.create(
                    user=manager,
                    title="هشدار انقضای دارو",
                    message=f"داروی {instance.name} منقضی شده است",
                    notification_type="error",
                    is_read=False
                )
    except Exception as e:
        print(f"Error in handle_medicine_notifications: {str(e)}")


@receiver(pre_save, sender=Medicine)
def check_medicine_expiry(sender, instance, **kwargs):
    """بررسی خودکار تاریخ انقضای داروها"""
    if instance.pk:  # فقط برای بروزرسانی رکوردهای موجود
        try:
            old_instance = Medicine.objects.get(pk=instance.pk)
            
            # بررسی تغییر تاریخ انقضا به تاریخی در گذشته
            if not old_instance.is_expired() and instance.is_expired():
                instance.is_active = False
                
                # دریافت گروه‌های مدیر HSE و مدیر اورژانس
                hse_group = Group.objects.filter(name='مدیر HSE').first()
                emergency_group = Group.objects.filter(name='مدیر اورژانس').first()
                
                # دریافت کاربران این گروه‌ها
                managers = []
                if hse_group:
                    managers.extend(User.objects.filter(groups=hse_group))
                if emergency_group:
                    managers.extend(User.objects.filter(groups=emergency_group))
                
                # اگر هیچ مدیری پیدا نشد، از همه کاربران ادمین استفاده می‌کنیم
                if not managers:
                    managers = User.objects.filter(is_superuser=True)
                
                for manager in managers:
                    Notification.objects.create(
                        user=manager,
                        title="تغییر تاریخ انقضای دارو",
                        message=f"داروی {instance.name} با تاریخ انقضای جدید، منقضی شده محسوب می‌شود و غیرفعال شد.",
                        notification_type="warning",
                        is_read=False
                    )
        except Exception as e:
            print(f"Error in check_medicine_expiry: {str(e)}")


@receiver(post_save, sender=MedicineUsage)
def handle_critical_usage(sender, instance, created, **kwargs):
    """هشدار برای مصرف دارویی که موجودی آن به حد بحرانی رسیده"""
    if created and instance.medicine.is_critical():
        try:
            # دریافت گروه‌های مدیر HSE و مدیر اورژانس
            hse_group = Group.objects.filter(name='مدیر HSE').first()
            emergency_group = Group.objects.filter(name='مدیر اورژانس').first()
            
            # دریافت کاربران این گروه‌ها
            managers = []
            if hse_group:
                managers.extend(User.objects.filter(groups=hse_group))
            if emergency_group:
                managers.extend(User.objects.filter(groups=emergency_group))
            
            # اگر هیچ مدیری پیدا نشد، از همه کاربران ادمین استفاده می‌کنیم
            if not managers:
                managers = User.objects.filter(is_superuser=True)
            
            for manager in managers:
                Notification.objects.create(
                    user=manager,
                    title="موجودی بحرانی دارو پس از مصرف",
                    message=f"پس از مصرف {instance.quantity} عدد، موجودی داروی {instance.medicine.name} به حد بحرانی ({instance.medicine.quantity} از {instance.medicine.critical_threshold}) رسیده است.",
                    notification_type="warning",
                    is_read=False
                )
        except Exception as e:
            print(f"Error in handle_critical_usage: {str(e)}") 