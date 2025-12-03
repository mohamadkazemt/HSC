"""
Celery Tasks برای Emergency Services
"""

from celery import shared_task
from django.utils import timezone
from django.core.management import call_command
from emergency_services.models import Medicine, ExpiredMedicineLog
from dashboard.models import Notification
from django.contrib.auth.models import User, Group
import logging

logger = logging.getLogger(__name__)


@shared_task
def cleanup_expired_medicines_task():
    """
    Task Celery برای حذف خودکار داروهای منقضی
    توصیه: هر روز در ساعت 2 صبح اجرا شود
    """
    try:
        # یافتن داروهای منقضی
        expired_medicines = Medicine.objects.filter(expiry_date__lt=timezone.now().date())
        
        if not expired_medicines.exists():
            logger.info('✓ هیچ دارویی برای حذف یافت نشد')
            return {'status': 'success', 'deleted_count': 0}
        
        expired_count = expired_medicines.count()
        logger.info(f'⚠️  {expired_count} دارو منقضی یافت شد')
        
        # دریافت نام‌های داروهای منقضی
        medicines_list = []
        for medicine in expired_medicines:
            medicines_list.append({
                'name': medicine.name,
                'category': medicine.category.name if medicine.category else 'بدون دسته‌بندی',
                'expiry_date': medicine.expiry_date,
                'quantity': medicine.quantity,
            })
        
        medicines_names = ', '.join([m['name'] for m in medicines_list[:5]])
        if expired_count > 5:
            medicines_names += f', و {expired_count - 5} دارو دیگر'
        
        # دریافت مدیران برای ارسال اطلاع‌رسانی
        try:
            hse_group = Group.objects.get(name='مدیر HSE')
            emergency_group = Group.objects.get(name='مدیر اورژانس')
            inspector_group = Group.objects.get(name='بازرس HSE')
            
            hse_managers = User.objects.filter(groups=hse_group)
            emergency_managers = User.objects.filter(groups=emergency_group)
            inspectors = User.objects.filter(groups=inspector_group)
            
            managers = list(hse_managers) + list(emergency_managers)
            all_users = managers + list(inspectors)
        except Group.DoesNotExist:
            all_users = []
            managers = []
            logger.warning('⚠️  گروه‌های مدیریت یافت نشدند')
        
        # ثبت لاگ برای هر دارو منقضی قبل از حذف
        for medicine in expired_medicines:
            ExpiredMedicineLog.objects.create(
                medicine_name=medicine.name,
                medicine_category=medicine.category.name if medicine.category else 'بدون دسته‌بندی',
                quantity=medicine.quantity,
                expiry_date=medicine.expiry_date,
                disposal_date=timezone.now().date(),
                disposal_method='deleted',
                notes=f'حذف خودکار توسط سیستم در {timezone.now()}',
                disposal_by_user=None
            )
        
        # ارسال اطلاع‌رسانی درباره حذف شدن به تمام مدیران و بازرسان
        for user in all_users:
            try:
                is_inspector = user.groups.filter(name='بازرس HSE').exists()
                notification_type = 'warning' if is_inspector else 'info'
                
                title = '🔴 داروهای منقضی حذف شدند' if is_inspector else 'داروهای منقضی حذف شدند'
                
                Notification.objects.create(
                    user=user,
                    title=title,
                    message=f'{expired_count} دارو منقضی حذف شدند: {medicines_names}\n\nلطفاً گزارش داروهای منقضی را بررسی کنید.',
                    notification_type=notification_type,
                    is_read=False
                )
            except Exception as e:
                logger.warning(f'خطا در ارسال اطلاع‌رسانی به {user.username}: {str(e)}')
        
        # حذف داروها
        deleted_count, _ = expired_medicines.delete()
        
        logger.info(f'✓ {deleted_count} دارو منقضی با موفقیت حذف شد و ثبت شد')
        
        return {
            'status': 'success',
            'deleted_count': deleted_count,
            'managers_notified': len(managers),
            'inspectors_notified': len(list(inspectors))
        }
    
    except Exception as e:
        logger.error(f'خطا در cleanup_expired_medicines_task: {str(e)}')
        return {
            'status': 'error',
            'error': str(e)
        }


@shared_task
def check_medicine_stock_levels_task():
    """
    Task Celery برای بررسی سطح موجودی داروها
    و ارسال هشدار برای داروهای بحرانی
    توصیه: هر روز در ساعت 8 صبح اجرا شود
    """
    try:
        # یافتن داروهای فعال و بحرانی
        from django.db.models import F
        critical_medicines = Medicine.objects.filter(
            is_active=True,
            quantity__lte=F('critical_threshold')
        )
        
        if not critical_medicines.exists():
            logger.info('✓ هیچ دارویی در سطح بحرانی یافت نشد')
            return {'status': 'success', 'critical_count': 0}
        
        critical_count = critical_medicines.count()
        logger.warning(f'⚠️  {critical_count} دارو در سطح بحرانی موجودی است')
        
        # دریافت مدیران و بازرسان
        try:
            hse_group = Group.objects.get(name='مدیر HSE')
            emergency_group = Group.objects.get(name='مدیر اورژانس')
            inspector_group = Group.objects.get(name='بازرس HSE')
            
            hse_managers = User.objects.filter(groups=hse_group)
            emergency_managers = User.objects.filter(groups=emergency_group)
            inspectors = User.objects.filter(groups=inspector_group)
            
            managers = list(hse_managers) + list(emergency_managers)
            all_users = managers + list(inspectors)
        except Group.DoesNotExist:
            all_users = []
        
        # ارسال اطلاع‌رسانی برای هر دارو بحرانی
        notified_count = 0
        for medicine in critical_medicines:
            unit_display = "سی‌سی" if medicine.drug_type == 'Liquid' else "عدد"
            
            for user in all_users:
                try:
                    # بررسی اینکه اطلاع‌رسانی قبلی وجود دارد یا نه
                    existing_notification = Notification.objects.filter(
                        user=user,
                        title__contains=medicine.name,
                        is_read=False,
                        created_at__date=timezone.now().date()
                    ).exists()
                    
                    if not existing_notification:
                        Notification.objects.create(
                            user=user,
                            title=f'⚠️ هشدار موجودی دارو: {medicine.name}',
                            message=f'موجودی داروی {medicine.name} به {medicine.quantity} {unit_display} رسیده است (حد بحرانی: {medicine.critical_threshold})',
                            notification_type='warning',
                            is_read=False
                        )
                        notified_count += 1
                except Exception as e:
                    logger.warning(f'خطا در ارسال اطلاع‌رسانی برای {medicine.name}: {str(e)}')
        
        logger.info(f'✓ {notified_count} اطلاع‌رسانی برای موجودی بحرانی ارسال شد')
        
        return {
            'status': 'success',
            'critical_count': critical_count,
            'notifications_sent': notified_count
        }
    
    except Exception as e:
        logger.error(f'خطا در check_medicine_stock_levels_task: {str(e)}')
        return {
            'status': 'error',
            'error': str(e)
        }


@shared_task
def mark_expired_medicines_inactive_task():
    """
    Task Celery برای تعطیل کردن داروهای منقضی
    (بجای حذف، وضعیت آن‌ها را غیرفعال کنید)
    توصیه: هر ساعت یک بار اجرا شود
    """
    try:
        # یافتن داروهای منقضی فعال
        expired_medicines = Medicine.objects.filter(
            expiry_date__lt=timezone.now().date(),
            is_active=True
        )
        
        if not expired_medicines.exists():
            logger.info('✓ هیچ دارویی برای تعطیل یافت نشد')
            return {'status': 'success', 'deactivated_count': 0}
        
        expired_count = expired_medicines.count()
        
        # تعطیل کردن داروها
        deactivated_count = expired_medicines.update(is_active=False)
        
        logger.info(f'✓ {deactivated_count} دارو منقضی تعطیل شد')
        
        return {
            'status': 'success',
            'deactivated_count': deactivated_count
        }
    
    except Exception as e:
        logger.error(f'خطا در mark_expired_medicines_inactive_task: {str(e)}')
        return {
            'status': 'error',
            'error': str(e)
        }
