# corrective_actions/tasks.py
"""
Celery tasks برای خودکارسازی اقدامات اصلاحی
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging
import time

logger = logging.getLogger(__name__)

# Batch size for processing anomalies (to avoid API rate limits)
BATCH_SIZE = 50
# Rate limiting: sleep between AI requests (in seconds)
RATE_LIMIT_DELAY = 10


@shared_task(bind=True, max_retries=3)
def check_unresolved_anomalies(self, days_threshold: int = 5):
    """
    بررسی آنومالی‌های رفع نشده و ایجاد اقدام اصلاحی
    
    این task به صورت batch کار می‌کند تا از rate limiting جلوگیری کند:
    - فقط 50 رکورد در هر اجرا پردازش می‌شود
    - بین هر درخواست AI، 10 ثانیه تاخیر وجود دارد
    
    Args:
        days_threshold: تعداد روزهای مجاز قبل از ایجاد اقدام اصلاحی (پیش‌فرض: 5)
    """
    try:
        from anomalis.models import Anomaly
        from corrective_actions.ai_automation import CorrectiveActionAutomation
        from dashboard.notification_utils import safe_notification
        
        if Anomaly is None:
            logger.warning("مدل Anomaly در دسترس نیست")
            return
        
        automation = CorrectiveActionAutomation()
        
        # تاریخ حداقل (5 روز پیش)
        threshold_date = timezone.now() - timedelta(days=days_threshold)
        
        # پیدا کردن آنومالی‌های ناایمن که رفع نشده‌اند و اقدام اصلاحی ندارند
        # بررسی از طریق related_anomaly در CorrectiveAction جدید
        from corrective_actions.models import CorrectiveAction
        existing_anomaly_ids = CorrectiveAction.objects.filter(
            related_anomaly__isnull=False
        ).values_list('related_anomaly_id', flat=True)
        
        # IMPORTANT: Limit to first 50 records only (batching strategy)
        # This prevents processing 5000+ records at once and causing 429 errors
        unresolved_anomalies = Anomaly.objects.filter(
            action=False,  # ناایمن (False = ناایمن)
            created_at__lte=threshold_date,  # بیشتر از 5 روز پیش
        ).exclude(
            id__in=existing_anomaly_ids  # آنومالی‌هایی که قبلاً اقدام اصلاحی دارند
        ).select_related('location', 'section', 'created_by', 'followup', 'priority')[:BATCH_SIZE]
        
        created_count = 0
        total_checked = len(unresolved_anomalies)
        
        logger.info(f"شروع پردازش {total_checked} آنومالی (batch size: {BATCH_SIZE})")
        
        for index, anomaly in enumerate(unresolved_anomalies, start=1):
            try:
                # Rate limiting: Add delay between AI requests to avoid 429 errors
                # Skip delay for the first request
                if index > 1:
                    logger.debug(f"Rate limiting: waiting {RATE_LIMIT_DELAY} seconds before next AI request...")
                    time.sleep(RATE_LIMIT_DELAY)
                
                logger.info(f"پردازش آنومالی {anomaly.id} ({index}/{total_checked})")
                
                corrective_action = automation.create_corrective_action_from_anomaly(
                    anomaly=anomaly,
                    auto_generate=True
                )
                
                if corrective_action:
                    created_count += 1
                    
                    # ارسال اعلان به مسئول پیگیری
                    if anomaly.followup and anomaly.followup.user:
                        safe_notification(
                            user=anomaly.followup.user,
                            title='اقدام اصلاحی خودکار ایجاد شد',
                            message=f'برای آنومالی #{anomaly.id} اقدام اصلاحی {corrective_action.tracking_code} به صورت خودکار ایجاد شد.',
                            url=f'/corrective-actions/{corrective_action.pk}/',
                            actor=None,
                            skip_actor_check=True
                        )
                    
                    logger.info(f"اقدام اصلاحی {corrective_action.tracking_code} برای آنومالی {anomaly.id} ایجاد شد")
                    
            except Exception as e:
                logger.error(f"خطا در ایجاد اقدام اصلاحی برای آنومالی {anomaly.id}: {e}", exc_info=True)
                continue
        
        logger.info(f"بررسی آنومالی‌های رفع نشده: {created_count} اقدام اصلاحی ایجاد شد از {total_checked} آنومالی بررسی شده")
        return {
            'success': True,
            'created_count': created_count,
            'checked_count': total_checked,
            'batch_size': BATCH_SIZE,
            'message': f'پردازش {total_checked} آنومالی با batch size {BATCH_SIZE}'
        }
        
    except Exception as e:
        logger.error(f"خطا در task بررسی آنومالی‌های رفع نشده: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
def check_high_risk_assessments(self):
    """
    بررسی ریسک‌های زرد و قرمز و ایجاد اقدام اصلاحی با AI
    """
    try:
        from risk_assessment.models import RiskAssessment
        from corrective_actions.ai_automation import CorrectiveActionAutomation
        from dashboard.notification_utils import safe_notification
        
        if RiskAssessment is None:
            logger.warning("مدل RiskAssessment در دسترس نیست")
            return
        
        automation = CorrectiveActionAutomation()
        
        # پیدا کردن ریسک‌های زرد (warning) و قرمز (danger) که اقدام اصلاحی ندارند
        # بررسی از طریق related_risk در CorrectiveAction
        from corrective_actions.models import CorrectiveAction
        existing_risk_ids = CorrectiveAction.objects.filter(
            related_risk__isnull=False
        ).values_list('related_risk_id', flat=True)
        
        high_risks = RiskAssessment.objects.filter(
            # ریسک‌های زرد یا قرمز
            risk_number__gte=5
        ).exclude(
            id__in=existing_risk_ids  # ریسک‌هایی که قبلاً اقدام اصلاحی دارند
        ).filter(
            # فقط ریسک‌های تأیید شده
            approval_status='approved'
        ).select_related('created_by', 'responsible_person', 'position')
        
        created_count = 0
        for risk in high_risks:
            try:
                # فقط برای ریسک‌های زرد و قرمز اقدام اصلاحی ایجاد کن
                risk_color = risk.get_risk_color()
                if risk_color not in ['warning', 'danger']:
                    continue
                
                # تولید اقدامات کنترلی با AI
                control_measures = automation.generate_control_measures_from_risk(risk)
                
                # اگر اقدامات کنترلی تولید شد، آنها را در ریسک ذخیره کن
                if control_measures:
                    if control_measures[0].get('description'):
                        risk.control_elimination = control_measures[0]['description']
                    if control_measures[1].get('description'):
                        risk.control_substitution = control_measures[1]['description']
                    if control_measures[2].get('description'):
                        risk.control_engineering = control_measures[2]['description']
                    if control_measures[3].get('description'):
                        risk.control_admin = control_measures[3]['description']
                    if control_measures[4].get('description'):
                        risk.control_ppe = control_measures[4]['description']
                    risk.save()
                
                # ایجاد اقدام اصلاحی
                corrective_action = automation.create_corrective_action_from_risk(
                    risk=risk,
                    auto_generate=True
                )
                
                if corrective_action:
                    created_count += 1
                    
                    # ارسال اعلان به مسئول
                    if risk.responsible_person and risk.responsible_person.user:
                        safe_notification(
                            user=risk.responsible_person.user,
                            title='اقدام اصلاحی خودکار ایجاد شد',
                            message=f'برای ریسک #{risk.id} (RPN: {risk.risk_number}) اقدام اصلاحی {corrective_action.tracking_code} به صورت خودکار ایجاد شد.',
                            url=f'/corrective-actions/{corrective_action.pk}/',
                            actor=None,
                            skip_actor_check=True
                        )
                    
                    logger.info(f"اقدام اصلاحی {corrective_action.tracking_code} برای ریسک {risk.id} ایجاد شد")
                    
            except Exception as e:
                logger.error(f"خطا در ایجاد اقدام اصلاحی برای ریسک {risk.id}: {e}", exc_info=True)
                continue
        
        logger.info(f"بررسی ریسک‌های بالا: {created_count} اقدام اصلاحی ایجاد شد")
        return {
            'success': True,
            'created_count': created_count,
            'checked_count': high_risks.count()
        }
        
    except Exception as e:
        logger.error(f"خطا در task بررسی ریسک‌های بالا: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60)
