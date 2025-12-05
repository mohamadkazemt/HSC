# corrective_actions/ai_helper.py
"""
سرویس هوش مصنوعی برای کمک به پر کردن فرم اقدام اصلاحی
"""
import logging
from typing import Dict, List, Optional, Any
from django.utils import timezone
from datetime import timedelta
from core.ai_service import get_ai_service
from .models import CorrectiveAction, ActionStep, SideEffectRisk
try:
    from anomalis.models import Anomaly
except ImportError:
    Anomaly = None

try:
    from hse_incidents.models import IncidentReport
except ImportError:
    IncidentReport = None

try:
    from risk_assessment.models import RiskAssessment
except ImportError:
    RiskAssessment = None

logger = logging.getLogger(__name__)


class CorrectiveActionAIHelper:
    """کلاس کمکی برای استفاده از AI در فرم اقدام اصلاحی"""
    
    def __init__(self):
        self.ai_service = get_ai_service()
    
    def _get_anomaly_context(self, anomaly_id: int) -> Optional[Dict]:
        """دریافت اطلاعات آنومالی مرتبط"""
        if Anomaly is None:
            return None
        try:
            # hse_type یک CharField است نه ForeignKey، پس نباید در select_related باشد
            anomaly = Anomaly.objects.select_related('location', 'section', 'anomalytype', 'anomalydescription', 'created_by', 'followup', 'priority').get(pk=anomaly_id)
            return {
                'type': 'anomaly',
                'id': anomaly.id,
                'description': anomaly.description or '',
                'location': str(anomaly.location) if anomaly.location else '',
                'hse_type': str(anomaly.hse_type) if anomaly.hse_type else '',
                'section': str(anomaly.section) if anomaly.section else '',
                'priority': str(anomaly.priority) if hasattr(anomaly, 'priority') and anomaly.priority else '',
                'created_at': str(anomaly.created_at) if hasattr(anomaly, 'created_at') else '',
            }
        except Anomaly.DoesNotExist:
            return None
    
    def _get_incident_context(self, incident_id: int) -> Optional[Dict]:
        """دریافت اطلاعات حادثه مرتبط"""
        if IncidentReport is None:
            return None
        try:
            incident = IncidentReport.objects.select_related('location', 'section').get(pk=incident_id)
            return {
                'type': 'incident',
                'id': incident.id,
                'incident_type': str(incident.incident_type) if hasattr(incident, 'incident_type') else '',
                'location': str(incident.location) if incident.location else '',
                'section': str(incident.section) if incident.section else '',
                'full_description': incident.full_description if hasattr(incident, 'full_description') else '',
                'initial_cause': incident.initial_cause if hasattr(incident, 'initial_cause') else '',
                'injury_type': str(incident.injury_type) if hasattr(incident, 'injury_type') else '',
                'incident_date': str(incident.incident_date) if hasattr(incident, 'incident_date') else '',
            }
        except IncidentReport.DoesNotExist:
            return None
    
    def _get_risk_context(self, risk_id: int) -> Optional[Dict]:
        """دریافت اطلاعات ریسک مرتبط"""
        if RiskAssessment is None:
            return None
        try:
            risk = RiskAssessment.objects.select_related('position', 'created_by', 'responsible_person').get(pk=risk_id)
            return {
                'type': 'risk',
                'id': risk.id,
                'hazard': risk.hazard if hasattr(risk, 'hazard') else '',
                'potential_event': risk.potential_event if hasattr(risk, 'potential_event') else '',
                'consequence': str(risk.consequence) if hasattr(risk, 'consequence') else '',
                'probability': risk.probability if hasattr(risk, 'probability') else None,
                'severity': risk.severity if hasattr(risk, 'severity') else None,
                'risk_number': risk.risk_number if hasattr(risk, 'risk_number') else None,
                'risk_level': risk.risk_level if hasattr(risk, 'risk_level') else '',
                'activity_component': risk.activity_component if hasattr(risk, 'activity_component') else '',
                'existing_controls': risk.existing_controls if hasattr(risk, 'existing_controls') else '',
                'control_elimination': risk.control_elimination if hasattr(risk, 'control_elimination') else '',
                'control_substitution': risk.control_substitution if hasattr(risk, 'control_substitution') else '',
                'control_engineering': risk.control_engineering if hasattr(risk, 'control_engineering') else '',
                'control_admin': risk.control_admin if hasattr(risk, 'control_admin') else '',
                'control_ppe': risk.control_ppe if hasattr(risk, 'control_ppe') else '',
                'position': str(risk.position) if hasattr(risk, 'position') and risk.position else '',
            }
        except RiskAssessment.DoesNotExist:
            return None
    
    def generate_corrective_action_data(
        self,
        related_anomaly_id: int = None,
        related_incident_id: int = None,
        related_risk_id: int = None,
        user_description: str = None
    ) -> Dict[str, Any]:
        """
        تولید داده‌های اقدام اصلاحی با استفاده از AI
        
        Returns:
            دیکشنری شامل پیشنهادات برای پر کردن فرم
        """
        context = {}
        
        # جمع‌آوری اطلاعات مرتبط
        if related_anomaly_id:
            context['anomaly'] = self._get_anomaly_context(related_anomaly_id)
        if related_incident_id:
            context['incident'] = self._get_incident_context(related_incident_id)
        if related_risk_id:
            context['risk'] = self._get_risk_context(related_risk_id)
        if user_description:
            context['user_description'] = user_description
        
        # ساخت prompt برای AI
        system_prompt = """شما یک متخصص HSE (ایمنی، بهداشت و محیط زیست) هستید که در ایجاد اقدامات اصلاحی و پیشگیرانه تخصص دارید.
        شما باید بر اساس اطلاعات ارائه شده، اقدامات اصلاحی مناسب را پیشنهاد دهید.
        پاسخ شما باید به زبان فارسی و حرفه‌ای باشد."""
        
        prompt = """بر اساس اطلاعات زیر، یک اقدام اصلاحی/پیشگیرانه پیشنهاد دهید.

لطفاً برای هر مورد زیر پیشنهاد ارائه دهید:
1. نوع اقدام (اصلاح، اصلاحی، پیشگیرانه، یا توصیه بهبود)
2. موضوع (کیفیت یا ایمنی، بهداشت و محیط زیست)
3. ورودی عدم انطباق (ممیزی، رویدادها و حوادث، ریسک‌ها، بازرسی، شکایات، یا سایر)
4. شرح عدم انطباق (توضیح کامل و دقیق)
5. علل ریشه‌ای عدم انطباق (تحلیل عمیق علل اصلی)
6. مراحل اقدام (لیست اقدامات لازم با مسئول و مهلت)
7. ریسک‌های ناشی از اقدام (در صورت وجود)

پاسخ را به صورت JSON با ساختار زیر برگردانید:
{
    "action_type": "corrective|preventive|correction|improvement",
    "topic": "hse|quality",
    "source": "audit|incident|risk|inspection|feedback|other",
    "description": "شرح کامل عدم انطباق",
    "root_cause_analysis": "تحلیل علل ریشه‌ای",
    "action_steps": [
        {
            "description": "شرح اقدام",
            "deadline_days": 7  // تعداد روز تا مهلت
        }
    ],
    "side_effect_risks": [
        {
            "hazard": "خطر",
            "event": "رویداد",
            "consequence": "پیامد",
            "control_measure": "اقدام کنترلی"
        }
    ]
}"""
        
        result = self.ai_service.generate_json(
            prompt=prompt,
            system_prompt=system_prompt,
            context=context,
            temperature=0.7
        )
        
        if not result:
            # در صورت خطا، پیشنهادات پیش‌فرض
            result = self._get_default_suggestions(context)
        else:
            # اعتبارسنجی و اصلاح داده‌ها
            result = self._validate_and_fix_suggestions(result, context)
        
        # اگر action_steps خالی است، با AI تولید کن
        if not result.get('action_steps'):
            try:
                action_steps = self.generate_action_steps(
                    description=result.get('description', ''),
                    root_cause=result.get('root_cause_analysis', '')
                )
                result['action_steps'] = action_steps
            except Exception as e:
                logger.warning(f"خطا در تولید action_steps: {e}")
                # پیشنهادات پیش‌فرض
                result['action_steps'] = [
                    {'description': 'بررسی و تحلیل دقیق مشکل', 'deadline_days': 3},
                    {'description': 'اجرای اقدامات اصلاحی', 'deadline_days': 7},
                    {'description': 'بررسی اثربخشی اقدامات', 'deadline_days': 14},
                ]
        
        # اگر side_effect_risks خالی است، با AI تولید کن
        if not result.get('side_effect_risks'):
            try:
                side_effect_risks = self.generate_side_effect_risks(
                    description=result.get('description', ''),
                    action_steps=result.get('action_steps', [])
                )
                result['side_effect_risks'] = side_effect_risks
            except Exception as e:
                logger.warning(f"خطا در تولید side_effect_risks: {e}")
                result['side_effect_risks'] = []
        
        return result
    
    def _get_default_suggestions(self, context: Dict) -> Dict[str, Any]:
        """پیشنهادات پیش‌فرض در صورت خطا در AI"""
        suggestions = {
            'action_type': 'corrective',
            'topic': 'hse',
            'source': 'other',
            'description': '',
            'root_cause_analysis': '',
            'action_steps': [],
            'side_effect_risks': []
        }
        
        if 'anomaly' in context:
            anomaly = context['anomaly']
            suggestions['source'] = 'inspection'
            suggestions['description'] = f"آنومالی در {anomaly.get('location', '')}: {anomaly.get('description', '')}"
            suggestions['action_type'] = 'corrective'
        elif 'incident' in context:
            incident = context['incident']
            suggestions['source'] = 'incident'
            suggestions['description'] = f"حادثه در {incident.get('location', '')}: {incident.get('full_description', '')}"
            suggestions['action_type'] = 'corrective'
        elif 'risk' in context:
            risk = context['risk']
            suggestions['source'] = 'risk'
            suggestions['description'] = f"ریسک شناسایی شده: {risk.get('hazard', '')}"
            suggestions['action_type'] = 'preventive'
        
        return suggestions
    
    def _validate_and_fix_suggestions(self, result: Dict, context: Dict) -> Dict[str, Any]:
        """اعتبارسنجی و اصلاح پیشنهادات AI"""
        # اعتبارسنجی action_type
        valid_action_types = ['correction', 'corrective', 'preventive', 'improvement']
        if result.get('action_type') not in valid_action_types:
            result['action_type'] = 'corrective'
        
        # اعتبارسنجی topic
        valid_topics = ['quality', 'hse']
        if result.get('topic') not in valid_topics:
            result['topic'] = 'hse'
        
        # اعتبارسنجی source
        valid_sources = ['audit', 'incident', 'risk', 'inspection', 'feedback', 'other']
        if result.get('source') not in valid_sources:
            # تعیین خودکار source بر اساس context
            if 'incident' in context:
                result['source'] = 'incident'
            elif 'risk' in context:
                result['source'] = 'risk'
            elif 'anomaly' in context:
                result['source'] = 'inspection'
            else:
                result['source'] = 'other'
        
        # اطمینان از وجود فیلدهای ضروری
        if 'description' not in result or not result['description']:
            result['description'] = 'شرح عدم انطباق'
        
        if 'root_cause_analysis' not in result:
            result['root_cause_analysis'] = ''
        
        if 'action_steps' not in result:
            result['action_steps'] = []
        
        if 'side_effect_risks' not in result:
            result['side_effect_risks'] = []
        
        # اعتبارسنجی action_steps
        for step in result.get('action_steps', []):
            if 'description' not in step:
                step['description'] = 'اقدام اصلاحی'
            if 'deadline_days' not in step or not isinstance(step['deadline_days'], int):
                step['deadline_days'] = 7
        
        return result
    
    def generate_root_cause_analysis(self, description: str, context: Dict = None) -> str:
        """تولید تحلیل علل ریشه‌ای با استفاده از AI"""
        system_prompt = """شما یک متخصص تحلیل علل ریشه‌ای (Root Cause Analysis) در زمینه HSE هستید.
        شما باید علل اصلی مشکلات را شناسایی و تحلیل کنید."""
        
        prompt = f"""بر اساس شرح عدم انطباق زیر، تحلیل علل ریشه‌ای ارائه دهید:

{description}

لطفاً علل ریشه‌ای را به صورت ساختاریافته و حرفه‌ای تحلیل کنید. پاسخ باید به زبان فارسی باشد."""
        
        result = self.ai_service.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            context=context,
            temperature=0.7
        )
        
        return result or 'تحلیل علل ریشه‌ای نیاز به بررسی بیشتر دارد.'
    
    def generate_action_steps(self, description: str, root_cause: str = None) -> List[Dict]:
        """تولید مراحل اقدام با استفاده از AI"""
        system_prompt = """شما یک متخصص HSE هستید که در برنامه‌ریزی اقدامات اصلاحی تخصص دارید."""
        
        prompt = f"""بر اساس شرح عدم انطباق و علل ریشه‌ای زیر، مراحل اقدام اصلاحی را پیشنهاد دهید:

شرح عدم انطباق:
{description}

علل ریشه‌ای:
{root_cause or 'در دست بررسی'}

لطفاً 3 تا 5 مرحله اقدام عملی و قابل اجرا پیشنهاد دهید. هر مرحله باید شامل:
- شرح اقدام
- مدت زمان تقریبی (به روز)

پاسخ را به صورت JSON با ساختار زیر برگردانید:
{{
    "action_steps": [
        {{
            "description": "شرح اقدام",
            "deadline_days": 7
        }}
    ]
}}"""
        
        result = self.ai_service.generate_json(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7
        )
        
        if result and 'action_steps' in result:
            return result['action_steps']
        
        # پیشنهادات پیش‌فرض
        return [
            {'description': 'بررسی و تحلیل دقیق مشکل', 'deadline_days': 3},
            {'description': 'اجرای اقدامات اصلاحی', 'deadline_days': 7},
            {'description': 'بررسی اثربخشی اقدامات', 'deadline_days': 14},
        ]
    
    def generate_side_effect_risks(self, description: str, action_steps: List[Dict] = None) -> List[Dict]:
        """تولید ریسک‌های ناشی از اقدام با استفاده از AI"""
        system_prompt = """شما یک متخصص HSE هستید که در شناسایی ریسک‌های ناشی از اقدامات اصلاحی تخصص دارید.
        شما باید ریسک‌های احتمالی که ممکن است از اجرای اقدامات اصلاحی ایجاد شود را شناسایی کنید."""
        
        action_steps_text = ""
        if action_steps:
            action_steps_text = "\nمراحل اقدام:\n"
            for i, step in enumerate(action_steps, 1):
                action_steps_text += f"{i}. {step.get('description', '')}\n"
        
        prompt = f"""بر اساس شرح عدم انطباق و مراحل اقدام زیر، ریسک‌های ناشی از اقدام را شناسایی کنید:

شرح عدم انطباق:
{description}
{action_steps_text}

لطفاً ریسک‌های احتمالی که ممکن است از اجرای این اقدامات ایجاد شود را شناسایی کنید.
برای هر ریسک، موارد زیر را مشخص کنید:
- خطر/جنبه (Hazard/Aspect)
- رویداد احتمالی (Event)
- پیامد (Consequence)
- اقدام کنترلی پیشنهادی (Control Measure)

پاسخ را به صورت JSON با ساختار زیر برگردانید:
{{
    "side_effect_risks": [
        {{
            "hazard": "خطر/جنبه",
            "event": "رویداد احتمالی",
            "consequence": "پیامد",
            "control_measure": "اقدام کنترلی پیشنهادی"
        }}
    ]
}}

اگر ریسک ناشی از اقدامی وجود ندارد، لیست خالی برگردانید: {{"side_effect_risks": []}}"""
        
        result = self.ai_service.generate_json(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7
        )
        
        if result and 'side_effect_risks' in result:
            return result['side_effect_risks']
        
        # اگر AI چیزی تولید نکرد، لیست خالی برگردان
        return []
