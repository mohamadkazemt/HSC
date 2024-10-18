from sms_ir import SmsIr
from django.conf import settings

sms_ir = SmsIr(settings.SMS_API_KEY, settings.SMS_LINE_NUMBER)

def send_sms(phone_number, message):
    """
    ارسال پیامک به شماره مشخص
    """
    result = sms_ir.send_sms(phone_number, message, settings.SMS_LINE_NUMBER)
    return result
