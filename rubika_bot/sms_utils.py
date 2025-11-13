from sms_ir import SmsIr
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

sms_ir = SmsIr(api_key=settings.SMSIR_API_KEY, linenumber=settings.SMSIR_LINE_NUMBER)

RUBIKA_CONNECTION_TEMPLATE = 999999

def send_connection_code_sms(mobile_number, connection_code):
    """
    ارسال کد اتصال روبیکا از طریق SMS
    """
    try:
        logger.info(f"شروع ارسال کد اتصال به شماره {mobile_number}")
        
        parameters = [
            {"Name": "CODE", "Value": connection_code}
        ]
        
        response = sms_ir.send_verify_code(
            number=mobile_number,
            template_id=RUBIKA_CONNECTION_TEMPLATE,
            parameters=parameters
        )
        
        if response.status_code == 200:
            response_data = response.json()
            logger.debug(f"پاسخ SMS.ir: {response_data}")
            
            if response_data.get("status") == 1 and response_data.get("message") == "موفق":
                logger.info(f"کد اتصال به {mobile_number} با موفقیت ارسال شد.")
                return True
            else:
                error_message = response_data.get("message", "خطای نامشخص")
                logger.error(f"خطا در ارسال کد اتصال به {mobile_number}: {error_message}")
                return False
        else:
            logger.error(f"خطا در ارسال کد اتصال: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.exception(f"خطا در ارسال کد اتصال: {e}")
        return False
