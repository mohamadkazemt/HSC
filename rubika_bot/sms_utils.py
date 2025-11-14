from sms_ir import SmsIr
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

sms_ir = SmsIr(api_key=settings.SMSIR_API_KEY, linenumber=settings.SMSIR_LINE_NUMBER)

RUBIKA_CONNECTION_TEMPLATE = 920200

def send_connection_code_sms(mobile_number, connection_code):
    """
    ارسال کد اتصال روبیکا از طریق SMS
    
    قالب پیامک در پنل SMS.ir باید به این صورت باشد:
    ---
    کد اتصال روبیکا: #CODE#
    این کد تا 60 دقیقه معتبر است.
    https://miepcoj.ir/
    ---
    پارامتر: CODE
    
    توضیح: کد اتصال 32 کاراکتر است و در یک پارامتر قرار می‌گیرد.
    """
    try:
        logger.info(f"📱 شروع ارسال کد اتصال به شماره {mobile_number}")
        logger.info(f"📝 Template ID: {RUBIKA_CONNECTION_TEMPLATE}")
        logger.info(f"🔑 Connection code length: {len(connection_code)}")
        
        # ارسال کد کامل در یک پارامتر (محدودیت SMS.ir: 64 کاراکتر)
        parameters = [
            {"Name": "CODE", "Value": connection_code}
        ]
        
        logger.info(f"📤 Sending SMS with parameters: {parameters}")
        
        response = sms_ir.send_verify_code(
            number=mobile_number,
            template_id=RUBIKA_CONNECTION_TEMPLATE,
            parameters=parameters
        )
        
        logger.info(f"📨 Response status code: {response.status_code}")
        logger.info(f"📨 Response text: {response.text}")
        
        if response.status_code == 200:
            response_data = response.json()
            logger.info(f"✅ پاسخ SMS.ir: {response_data}")
            
            if response_data.get("status") == 1:
                logger.info(f"✅ کد اتصال به {mobile_number} با موفقیت ارسال شد.")
                return True
            else:
                error_message = response_data.get("message", "خطای نامشخص")
                logger.error(f"❌ خطا در ارسال کد اتصال به {mobile_number}: {error_message}")
                logger.error(f"❌ Full response: {response_data}")
                return False
        else:
            logger.error(f"❌ خطا در ارسال کد اتصال: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.exception(f"💥 خطا در ارسال کد اتصال: {e}")
        return False
