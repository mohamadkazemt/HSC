"""سرویس مرکزی ارسال پیامک برای کل سیستم.

تمام اپ‌ها باید از این ماژول برای ارسال پیامک قالبی استفاده کنند تا:
- تکرار کد حذف شود
- اعتبارسنجی شماره و پارامترها یکنواخت باشد
- لاگ‌ها متمرکز شوند
- محدودیت نرخ (rate limiting) اعمال گردد

در صورت نیاز به آسنکرون: از celery و تسک `dashboard.tasks.send_template_sms_task` استفاده کنید.
"""
import logging
import re
from typing import List, Dict, Any, Optional
from django.conf import settings
from sms_ir import SmsIr

logger = logging.getLogger('smsir')

_sms_ir_instance: Optional[SmsIr] = None

MOBILE_REGEX_IR = re.compile(r"^(?:\+?98|0)?9\d{9}$")


def _get_client() -> SmsIr:
    global _sms_ir_instance
    if _sms_ir_instance is None:
        _sms_ir_instance = SmsIr(api_key=getattr(settings, 'SMSIR_API_KEY', ''), linenumber=getattr(settings, 'SMSIR_LINE_NUMBER', ''))
    return _sms_ir_instance


def _is_valid_mobile(mobile: str) -> bool:
    return bool(mobile and MOBILE_REGEX_IR.match(mobile))


def _normalize_parameters(parameters: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    cleaned: List[Dict[str, str]] = []
    for p in parameters or []:
        name = str(p.get('Name', '')).strip()
        value = str(p.get('Value', '')).strip()
        if name and value:
            cleaned.append({'Name': name, 'Value': value})
    return cleaned


def send_template_sms(mobile_number: str, template_id: int, parameters: List[Dict[str, Any]], user_id: Optional[int] = None, request=None) -> bool:
    """ارسال پیامک قالبی با بررسی محدودیت نرخ و لاگ کامل.
    
    Args:
        mobile_number: شماره موبایل مقصد
        template_id: شناسه قالب پیامک
        parameters: لیست پارامترهای قالب
        user_id: شناسه کاربر (برای rate limiting و logging)
        request: Django request object (برای logging IP)
    
    Returns:
        True در صورت موفقیت، False در غیر این صورت
    """
    # Create SMS log entry
    from dashboard.models_sms import SMSLog
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    user_obj = None
    if user_id:
        try:
            user_obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            pass
    
    # ایجاد لاگ اولیه
    sms_log = SMSLog.objects.create(
        mobile_number=mobile_number,
        template_id=template_id,
        parameters=parameters,
        user=user_obj,
        status='pending',
        ip_address=request.META.get('REMOTE_ADDR') if request else None,
        user_agent=request.META.get('HTTP_USER_AGENT') if request else None,
    )
    
    # بررسی rate limiting
    from core.sms_throttle import check_sms_rate_limit, increment_sms_counters
    
    allowed, reason = check_sms_rate_limit(user_id=user_id, mobile=mobile_number)
    if not allowed:
        logger.warning(f"[SMS] Rate limit exceeded: {reason} (mobile={mobile_number}, user_id={user_id})")
        sms_log.mark_as_rate_limited(reason)
        return False
    
    if not _is_valid_mobile(mobile_number):
        logger.warning(f"[SMS] Invalid mobile: {mobile_number}")
        sms_log.mark_as_failed("شماره موبایل نامعتبر است")
        return False

    cleaned_parameters = _normalize_parameters(parameters)
    if not cleaned_parameters:
        logger.warning("[SMS] No valid parameters; aborting send")
        sms_log.mark_as_failed("پارامترهای معتبر یافت نشد")
        return False

    client = _get_client()

    try:
        response = client.send_verify_code(number=mobile_number, template_id=template_id, parameters=cleaned_parameters)
    except Exception as exc:  # pragma: no cover
        logger.exception(f"[SMS] Exception during send: {exc}")
        sms_log.mark_as_failed(str(exc))
        return False

    status_code = getattr(response, 'status_code', None)
    text = getattr(response, 'text', '')
    logger.debug(f"[SMS] Raw response status={status_code} body={text[:250]}")

    if status_code != 200:
        logger.error(f"[SMS] HTTP error status={status_code} body={text}")
        sms_log.mark_as_failed(f"خطای HTTP {status_code}")
        return False

    response_json: Optional[Dict[str, Any]] = None
    try:
        if hasattr(response, 'json'):
            response_json = response.json()
        elif isinstance(response, dict):
            response_json = response
    except Exception as parse_err:  # pragma: no cover
        logger.error(f"[SMS] JSON parse failed: {parse_err}")

    success = False
    if isinstance(response_json, dict):
        success = (response_json.get('IsSuccessful') is True or response_json.get('status') == 1)
    else:
        success = True  # fallback

    if success:
        # افزایش شمارنده‌ها و ثبت موفقیت در لاگ
        increment_sms_counters(user_id=user_id, mobile=mobile_number)
        
        track_id = None
        if isinstance(response_json, dict):
            track_id = response_json.get('VerificationCodeId') or response_json.get('MessageId') or response_json.get('id')
        
        sms_log.mark_as_sent(track_id=track_id, response_data=response_json)
        
        # افزایش شمارنده قالب اگر وجود دارد
        try:
            from dashboard.models_sms import SMSTemplate
            template = SMSTemplate.objects.filter(template_id=template_id).first()
            if template:
                template.increment_usage()
        except Exception:
            pass
        
        logger.info(f"[SMS] Sent template={template_id} to {mobile_number} track_id={track_id} log_id={sms_log.id}")
        return True

    error_message = None
    if isinstance(response_json, dict):
        error_message = response_json.get('Message') or response_json.get('message') or response_json.get('ErrorMessage')
    
    sms_log.mark_as_failed(error_message or 'خطای نامشخص')
    logger.error(f"[SMS] Failed to send to {mobile_number}: {error_message or 'unknown'} body={response_json}")
    return False

__all__ = ["send_template_sms"]
