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
    کد اتصال روبیکا:
    #CODE1##CODE2#
    معتبر تا 60 دقیقه
    ---
    پارامترها: CODE1, CODE2
    
    توضیح: چون کد اتصال 32 کاراکتر است و محدودیت هر پارامتر 25 کاراکتر است،
    کد را به دو قسمت تقسیم می‌کنیم.
    """
    try:
        logger.info(f"شروع ارسال کد اتصال به شماره {mobile_number}")
        
        # تقسیم کد به دو قسمت به دلیل محدودیت 25 کاراکتری SMS.ir
        code_part1 = connection_code[:25]  # 25 کاراکتر اول
        code_part2 = connection_code[25:]  # باقیمانده (7 کاراکتر)
        
        parameters = [
            {"Name": "CODE1", "Value": code_part1},
            {"Name": "CODE2", "Value": code_part2}
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
