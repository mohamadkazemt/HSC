from sms_ir import SmsIr
from django.conf import settings
import logging

logger = logging.getLogger('smsir')

# مقداردهی SMS.ir
sms_ir = SmsIr(api_key=settings.SMSIR_API_KEY, linenumber=settings.SMSIR_LINE_NUMBER)


def send_template_sms(mobile_number, template_id, parameters):
    """
    ارسال پیامک با قالب در SMS.ir
    """
    try:
        response = sms_ir.send_verify_code(
            number=mobile_number,
            template_id=template_id,
            parameters=parameters
        )
        if response.status_code == 200:
            response_data = response.json()
            logger.debug(f"پاسخ SMS.ir: {response_data}")
            if response_data.get("IsSuccessful"):
                logger.info(f"پیامک با قالب {template_id} به {mobile_number} با موفقیت ارسال شد.")
                return True
            else:
                logger.error(f"خطا در ارسال پیامک به {mobile_number}: {response_data.get('Message')}")
                return False
        else:
            logger.error(f"خطا در ارسال پیامک: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.exception(f"خطا در ارسال پیامک: {e}")
        return False
