# corrective_actions/ai_automation.py
"""
سرویس خودکارسازی اقدامات اصلاحی با استفاده از AI
"""
import logging
from typing import Dict, List, Optional, Any
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from core.ai_service import get_ai_service
from .models import CorrectiveAction, ActionStep, SideEffectRisk
from accounts.models import UserProfile

logger = logging.getLogger(__name__)

try:
    from anomalis.models import Anomaly
except ImportError:
    Anomaly = None

try:
    from risk_assessment.models import RiskAssessment
except ImportError:
    RiskAssessment = None

try:
    from anomalis.models import Anomaly
except ImportError:
    Anomaly = None

try:
    from risk_assessment.models import RiskAssessment
except ImportError:
    RiskAssessment = None


class CorrectiveActionAutomation:
    """کلاس برای خودکارسازی ایجاد اقدامات اصلاحی"""
    
    def __init__(self):
        self.ai_service = get_ai_service()
    
    def generate_tracking_code(self) -> str:
        """تولید شماره اقدام اصلاحی"""
        from django.utils import timezone
        import jdatetime
        import time
        
        today = timezone.now().date()
        jalali_date = jdatetime.date.fromgregorian(date=today)
        year = jalali_date.year % 100  # دو رقم آخر سال
        month = jalali_date.month
        day = jalali_date.day
        
        # شماره‌گذاری بر اساس تاریخ
        date_prefix = f"{year:02d}{month:02d}{day:02d}"
        
        # شمارش اقدامات امروز
        today_actions = CorrectiveAction.objects.filter(
            tracking_code__startswith=f"CA-{date_prefix}-"
        ).count()
        
        # استفاده از timestamp برای اطمینان از یکتایی
        import random
        timestamp_suffix = int(time.time() * 1000) % 10000  # 4 رقم آخر timestamp
        random_suffix = random.randint(100, 999)  # 3 رقم تصادفی
        
        sequence = today_actions + 1
        tracking_code = f"CA-{date_prefix}-{sequence:03d}-{timestamp_suffix:04d}-{random_suffix:03d}"
        
        # بررسی یکتایی (اگر تکراری بود، دوباره تولید کن)
        max_retries = 10
        retry_count = 0
        while CorrectiveAction.objects.filter(tracking_code=tracking_code).exists() and retry_count < max_retries:
            retry_count += 1
            timestamp_suffix = int(time.time() * 1000) % 10000
            random_suffix = random.randint(100, 999)
            sequence = today_actions + retry_count
            tracking_code = f"CA-{date_prefix}-{sequence:03d}-{timestamp_suffix:04d}-{random_suffix:03d}"
        
        return tracking_code
    
    def create_corrective_action_from_anomaly(
        self,
        anomaly: 'Anomaly',
        auto_generate: bool = True
    ) -> Optional[CorrectiveAction]:
        """
        ایجاد اقدام اصلاحی از آنومالی
        
        Args:
            anomaly: آنومالی مورد نظر
            auto_generate: آیا از AI برای تولید محتوا استفاده شود
        
        Returns:
            اقدام اصلاحی ایجاد شده یا None در صورت خطا
        """
        try:
            # بررسی اینکه آیا قبلاً اقدام اصلاحی ایجاد شده است
            # بررسی از طریق related_anomaly در CorrectiveAction جدید
            existing_action = CorrectiveAction.objects.filter(
                related_anomaly=anomaly
            ).first()
            
            if existing_action:
                logger.info(f"اقدام اصلاحی برای آنومالی {anomaly.id} قبلاً ایجاد شده است: {existing_action.tracking_code}")
                return existing_action
            
            # توجه: مدل قدیمی CorrectiveAction در anomalis یک ForeignKey اجباری است
            # پس همه آنومالی‌ها باید یک correctiveaction داشته باشند
            # اما ما می‌خواهیم اقدام اصلاحی جدید (در corrective_actions) ایجاد کنیم
            # پس این بررسی را skip می‌کنیم
            
            with transaction.atomic():
                # تولید داده‌ها با AI
                if auto_generate:
                    try:
                        from .ai_helper import CorrectiveActionAIHelper
                        ai_helper = CorrectiveActionAIHelper()
                        suggestions = ai_helper.generate_corrective_action_data(
                            related_anomaly_id=anomaly.id
                        )
                        # اگر AI خطا داد یا None برگشت، از پیش‌فرض استفاده کن
                        if not suggestions:
                            logger.warning(f"AI هیچ پیشنهادی نداد، از پیش‌فرض استفاده می‌شود")
                            suggestions = {}
                    except Exception as ai_error:
                        logger.error(f"خطا در تولید داده‌ها با AI: {ai_error}", exc_info=True)
                        suggestions = {}
                else:
                    suggestions = {}
                
                # اگر suggestions خالی است یا فیلدهای لازم را ندارد، از پیش‌فرض استفاده کن
                if not suggestions or not suggestions.get('description'):
                    suggestions = {
                        'action_type': suggestions.get('action_type', 'corrective') if suggestions else 'corrective',
                        'topic': suggestions.get('topic', 'hse') if suggestions else 'hse',
                        'source': suggestions.get('source', 'inspection') if suggestions else 'inspection',
                        'description': f"آنومالی در {anomaly.location.name if anomaly.location else 'نامشخص'}: {anomaly.description}",
                        'root_cause_analysis': suggestions.get('root_cause_analysis', 'نیاز به بررسی بیشتر') if suggestions else 'نیاز به بررسی بیشتر',
                        'action_steps': suggestions.get('action_steps', []) if suggestions else [],
                        'side_effect_risks': suggestions.get('side_effect_risks', []) if suggestions else []
                    }
                
                # اطمینان از وجود action_steps (حداقل 3 مورد)
                if not suggestions.get('action_steps'):
                    from .ai_helper import CorrectiveActionAIHelper
                    ai_helper = CorrectiveActionAIHelper()
                    try:
                        action_steps = ai_helper.generate_action_steps(
                            description=suggestions.get('description', ''),
                            root_cause=suggestions.get('root_cause_analysis', '')
                        )
                        suggestions['action_steps'] = action_steps
                    except:
                        # پیشنهادات پیش‌فرض
                        suggestions['action_steps'] = [
                            {'description': 'بررسی و تحلیل دقیق مشکل', 'deadline_days': 3},
                            {'description': 'اجرای اقدامات اصلاحی', 'deadline_days': 7},
                            {'description': 'بررسی اثربخشی اقدامات', 'deadline_days': 14},
                        ]
                
                # اطمینان از وجود side_effect_risks (اگر خالی است، با AI تولید کن)
                if not suggestions.get('side_effect_risks'):
                    from .ai_helper import CorrectiveActionAIHelper
                    ai_helper = CorrectiveActionAIHelper()
                    try:
                        side_effect_risks = ai_helper.generate_side_effect_risks(
                            description=suggestions.get('description', ''),
                            action_steps=suggestions.get('action_steps', [])
                        )
                        suggestions['side_effect_risks'] = side_effect_risks
                    except:
                        suggestions['side_effect_risks'] = []
                
                # ایجاد اقدام اصلاحی
                corrective_action = CorrectiveAction.objects.create(
                    tracking_code=self.generate_tracking_code(),
                    action_type=suggestions.get('action_type', 'corrective'),
                    topic=suggestions.get('topic', 'hse'),
                    source=suggestions.get('source', 'inspection'),
                    description=suggestions.get('description', anomaly.description),
                    root_cause_analysis=suggestions.get('root_cause_analysis', ''),
                    requester=anomaly.created_by if anomaly.created_by else None,
                    receiver=anomaly.followup if anomaly.followup else None,
                    related_anomaly=anomaly,
                    status='open'
                )
                
                # ایجاد مراحل اقدام
                today = timezone.now().date()
                for idx, step_data in enumerate(suggestions.get('action_steps', [])):
                    deadline_days = step_data.get('deadline_days', 7)
                    ActionStep.objects.create(
                        corrective_action=corrective_action,
                        description=step_data.get('description', f'اقدام {idx + 1}'),
                        responsible=anomaly.followup if anomaly.followup else None,
                        deadline=today + timedelta(days=deadline_days)
                    )
                
                # ایجاد ریسک‌های ناشی از اقدام
                for risk_data in suggestions.get('side_effect_risks', []):
                    SideEffectRisk.objects.create(
                        corrective_action=corrective_action,
                        hazard=risk_data.get('hazard', ''),
                        event=risk_data.get('event', ''),
                        consequence=risk_data.get('consequence', ''),
                        control_measure=risk_data.get('control_measure', '')
                    )
                
                logger.info(f"اقدام اصلاحی {corrective_action.tracking_code} از آنومالی {anomaly.id} ایجاد شد")
                return corrective_action
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"خطا در ایجاد اقدام اصلاحی از آنومالی {anomaly.id}: {error_msg}", exc_info=True)
            # نمایش خطا در console برای debugging
            import sys
            print(f"ERROR: {error_msg}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return None
    
    def create_corrective_action_from_risk(
        self,
        risk: 'RiskAssessment',
        auto_generate: bool = True
    ) -> Optional[CorrectiveAction]:
        """
        ایجاد اقدام اصلاحی از ریسک با استفاده از AI
        
        Args:
            risk: ریسک مورد نظر
            auto_generate: آیا از AI برای تولید محتوا استفاده شود
        
        Returns:
            اقدام اصلاحی ایجاد شده یا None در صورت خطا
        """
        try:
            # بررسی اینکه آیا قبلاً اقدام اصلاحی ایجاد شده است
            existing_action = CorrectiveAction.objects.filter(
                related_risk=risk
            ).first()
            
            if existing_action:
                logger.info(f"اقدام اصلاحی برای ریسک {risk.id} قبلاً ایجاد شده است: {existing_action.tracking_code}")
                return existing_action
            
            with transaction.atomic():
                # تولید داده‌ها با AI
                if auto_generate:
                    # ابتدا اقدامات کنترلی را با AI تولید کن (اگر وجود ندارند)
                    if not any([risk.control_elimination, risk.control_substitution, 
                               risk.control_engineering, risk.control_admin, risk.control_ppe]):
                        control_measures = self.generate_control_measures_from_risk(risk)
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
                    
                    from .ai_helper import CorrectiveActionAIHelper
                    ai_helper = CorrectiveActionAIHelper()
                    suggestions = ai_helper.generate_corrective_action_data(
                        related_risk_id=risk.id
                    )
                    
                    # استفاده از اقدامات کنترلی موجود در ریسک برای تولید مراحل اقدام
                    control_measures = []
                    if risk.control_elimination:
                        control_measures.append({
                            'type': 'حذف خطر',
                            'description': risk.control_elimination,
                            'priority': 1
                        })
                    if risk.control_substitution:
                        control_measures.append({
                            'type': 'جایگزینی',
                            'description': risk.control_substitution,
                            'priority': 2
                        })
                    if risk.control_engineering:
                        control_measures.append({
                            'type': 'کنترل مهندسی',
                            'description': risk.control_engineering,
                            'priority': 3
                        })
                    if risk.control_admin:
                        control_measures.append({
                            'type': 'کنترل اداری',
                            'description': risk.control_admin,
                            'priority': 4
                        })
                    if risk.control_ppe:
                        control_measures.append({
                            'type': 'لوازم حفاظت فردی',
                            'description': risk.control_ppe,
                            'priority': 5
                        })
                    
                    # اگر اقدامات کنترلی وجود دارد، از آنها برای تولید action_steps استفاده کن
                    if control_measures:
                        # اگر AI action_steps تولید نکرده یا خالی است، از control_measures استفاده کن
                        if not suggestions.get('action_steps'):
                            suggestions['action_steps'] = []
                        # اضافه کردن اقدامات کنترلی به action_steps
                        for measure in sorted(control_measures, key=lambda x: x['priority']):
                            suggestions['action_steps'].append({
                                'description': f"{measure['type']}: {measure['description']}",
                                'deadline_days': 7 + (measure['priority'] * 3)  # مهلت‌های متفاوت
                            })
                else:
                    suggestions = {
                        'action_type': 'preventive',
                        'topic': 'hse',
                        'source': 'risk',
                        'description': f"ریسک شناسایی شده: {risk.hazard}",
                        'root_cause_analysis': 'نیاز به بررسی بیشتر',
                        'action_steps': [],
                        'side_effect_risks': []
                    }
                    
                    # تولید action_steps از اقدامات کنترلی
                    if control_measures:
                        suggestions['action_steps'] = []
                        for measure in sorted(control_measures, key=lambda x: x['priority']):
                            suggestions['action_steps'].append({
                                'description': f"{measure['type']}: {measure['description']}",
                                'deadline_days': 7 + (measure['priority'] * 3)
                            })
                    else:
                        # اگر اقدامات کنترلی نداریم، با AI تولید کن
                        from .ai_helper import CorrectiveActionAIHelper
                        ai_helper = CorrectiveActionAIHelper()
                        try:
                            action_steps = ai_helper.generate_action_steps(
                                description=suggestions.get('description', ''),
                                root_cause=suggestions.get('root_cause_analysis', '')
                            )
                            suggestions['action_steps'] = action_steps
                        except:
                            suggestions['action_steps'] = [
                                {'description': 'بررسی و تحلیل دقیق مشکل', 'deadline_days': 3},
                                {'description': 'اجرای اقدامات اصلاحی', 'deadline_days': 7},
                                {'description': 'بررسی اثربخشی اقدامات', 'deadline_days': 14},
                            ]
                    
                    # تولید side_effect_risks
                    from .ai_helper import CorrectiveActionAIHelper
                    ai_helper = CorrectiveActionAIHelper()
                    try:
                        side_effect_risks = ai_helper.generate_side_effect_risks(
                            description=suggestions.get('description', ''),
                            action_steps=suggestions.get('action_steps', [])
                        )
                        suggestions['side_effect_risks'] = side_effect_risks
                    except:
                        suggestions['side_effect_risks'] = []
                
                # ایجاد اقدام اصلاحی
                corrective_action = CorrectiveAction.objects.create(
                    tracking_code=self.generate_tracking_code(),
                    action_type=suggestions.get('action_type', 'preventive'),
                    topic=suggestions.get('topic', 'hse'),
                    source=suggestions.get('source', 'risk'),
                    description=suggestions.get('description', f"ریسک: {risk.hazard}"),
                    root_cause_analysis=suggestions.get('root_cause_analysis', ''),
                    requester=risk.created_by if risk.created_by else None,
                    receiver=risk.responsible_person if risk.responsible_person else None,
                    related_risk=risk,
                    status='open'
                )
                
                # ایجاد مراحل اقدام
                today = timezone.now().date()
                for idx, step_data in enumerate(suggestions.get('action_steps', [])):
                    deadline_days = step_data.get('deadline_days', 7)
                    ActionStep.objects.create(
                        corrective_action=corrective_action,
                        description=step_data.get('description', f'اقدام {idx + 1}'),
                        responsible=risk.responsible_person if risk.responsible_person else None,
                        deadline=today + timedelta(days=deadline_days)
                    )
                
                # ایجاد ریسک‌های ناشی از اقدام
                for risk_data in suggestions.get('side_effect_risks', []):
                    SideEffectRisk.objects.create(
                        corrective_action=corrective_action,
                        hazard=risk_data.get('hazard', ''),
                        event=risk_data.get('event', ''),
                        consequence=risk_data.get('consequence', ''),
                        control_measure=risk_data.get('control_measure', '')
                    )
                
                # به‌روزرسانی ریسک
                risk.corrective_action_required = True
                risk.action_number = corrective_action.tracking_code
                risk.action_date = today
                if not risk.action_deadline:
                    # مهلت را بر اساس آخرین action step تنظیم کن
                    last_step = corrective_action.action_steps.order_by('-deadline').first()
                    if last_step:
                        risk.action_deadline = last_step.deadline
                risk.save()
                
                logger.info(f"اقدام اصلاحی {corrective_action.tracking_code} از ریسک {risk.id} ایجاد شد")
                return corrective_action
                
        except Exception as e:
            logger.error(f"خطا در ایجاد اقدام اصلاحی از ریسک {risk.id}: {e}", exc_info=True)
            return None
    
    def generate_control_measures_from_risk(self, risk: 'RiskAssessment') -> List[Dict]:
        """
        تولید اقدامات کنترلی از ریسک با استفاده از AI
        
        Returns:
            لیست اقدامات کنترلی (5 مورد: حذف، جایگزینی، مهندسی، اداری، PPE)
        """
        if not RiskAssessment:
            return []
        
        system_prompt = """شما یک متخصص HSE هستید که در شناسایی و پیشنهاد اقدامات کنترلی تخصص دارید.
        بر اساس سلسله مراتب کنترل (Hierarchy of Controls)، 5 نوع اقدام کنترلی را پیشنهاد دهید:
        1. حذف خطر (Elimination) - حذف کامل خطر
        2. جایگزینی (Substitution) - جایگزین کردن با چیز کم‌خطرتر
        3. کنترل مهندسی (Engineering Controls) - کنترل‌های فنی و مهندسی
        4. کنترل اداری (Administrative Controls) - دستورالعمل‌ها، آموزش، تابلوها
        5. لوازم حفاظت فردی (PPE) - تجهیزات حفاظت شخصی
        
        پاسخ باید به زبان فارسی و عملی باشد."""
        
        prompt = f"""بر اساس اطلاعات ریسک زیر، 5 اقدام کنترلی پیشنهاد دهید:

خطر: {risk.hazard}
رویداد احتمالی: {risk.potential_event}
پیامد: {risk.consequence}
احتمال: {risk.probability}
شدت: {risk.severity}
عدد ریسک: {risk.risk_number}
کنترل‌های موجود: {risk.existing_controls or 'ندارد'}

لطفاً برای هر یک از 5 نوع اقدام کنترلی، یک پیشنهاد عملی و قابل اجرا ارائه دهید.

پاسخ را به صورت JSON با ساختار زیر برگردانید:
{{
    "control_elimination": "اقدام حذف خطر",
    "control_substitution": "اقدام جایگزینی",
    "control_engineering": "اقدام کنترل مهندسی",
    "control_admin": "اقدام کنترل اداری",
    "control_ppe": "اقدام لوازم حفاظت فردی"
}}"""
        
        result = self.ai_service.generate_json(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7
        )
        
        if result:
            return [
                {'type': 'elimination', 'description': result.get('control_elimination', '')},
                {'type': 'substitution', 'description': result.get('control_substitution', '')},
                {'type': 'engineering', 'description': result.get('control_engineering', '')},
                {'type': 'admin', 'description': result.get('control_admin', '')},
                {'type': 'ppe', 'description': result.get('control_ppe', '')},
            ]
        
        return []
