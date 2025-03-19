from sms_ir import SmsIr
from django.conf import settings
import logging
import jdatetime

logger = logging.getLogger(__name__)

# مقداردهی SMS.ir
sms_ir = SmsIr(api_key=settings.SMSIR_API_KEY, linenumber=settings.SMSIR_LINE_NUMBER)

# شناسه قالب پیامک جلسات
MEETING_TEMPLATE = 226785  # قالب پیامک برای تمام عملیات جلسات

def send_template_sms(mobile_number, template_id, parameters):
    """
    ارسال پیامک با قالب در SMS.ir
    """
    try:
        print(f"\n=== شروع ارسال پیامک با قالب ===")
        print(f"شماره موبایل: {mobile_number}")
        print(f"شناسه قالب: {template_id}")
        print(f"پارامترها: {parameters}")
        
        response = sms_ir.send_verify_code(
            number=mobile_number,
            template_id=template_id,
            parameters=parameters
        )
        
        print(f"پاسخ API: {response.text}")
        
        if response.status_code == 200:
            response_data = response.json()  # تبدیل پاسخ به دیکشنری
            logger.debug(f"پاسخ SMS.ir: {response_data}")
            
            # بررسی موفقیت‌آمیز بودن ارسال پیامک
            if response_data.get("status") == 1 and response_data.get("message") == "موفق":
                logger.info(f"پیامک با قالب {template_id} به {mobile_number} با موفقیت ارسال شد.")
                print(f"پیامک با موفقیت ارسال شد")
                return True
            else:
                error_message = response_data.get("message", "خطای نامشخص")
                logger.error(f"خطا در ارسال پیامک به {mobile_number}: {error_message}")
                print(f"خطا در ارسال پیامک: {error_message}")
                return False
        else:
            logger.error(f"خطا در ارسال پیامک: {response.status_code} - {response.text}")
            print(f"خطا در ارسال پیامک: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.exception(f"خطا در ارسال پیامک: {e}")
        print(f"خطا در ارسال پیامک: {e}")
        import traceback
        print(f"جزئیات خطا: {traceback.format_exc()}")
        return False

def send_meeting_sms(mobile, status, meeting_id, meeting_title, date, time):
    """
    ارسال پیامک برای عملیات‌های جلسه با قالب جدید
    """
    try:
        print(f"\n=== شروع ارسال پیامک ===")
        print(f"شماره موبایل: {mobile}")
        print(f"وضعیت: {status}")
        print(f"شناسه جلسه: {meeting_id}")
        print(f"عنوان جلسه: {meeting_title}")
        print(f"تاریخ ورودی: {date}")
        print(f"زمان: {time}")
        
        if mobile:
            # تبدیل تاریخ به فرمت مورد نیاز (YYYY-MM-DD)
            try:
                if isinstance(date, str):
                    # اگر تاریخ به صورت رشته است، مستقیماً استفاده می‌کنیم
                    jalali_date = date
                else:
                    # اگر تاریخ به صورت شیء jdatetime است
                    jalali_date = f"{date.year}-{date.month:02d}-{date.day:02d}"
                print(f"تاریخ شمسی نهایی: {jalali_date}")
            except Exception as e:
                print(f"خطا در پردازش تاریخ: {str(e)}")
                return
            
            parameters = [
                {"Name": "STATUS", "Value": status},
                {"Name": "MEETING_TITLE", "Value": meeting_title},
                {"Name": "MEETING_DATE", "Value": jalali_date},
                {"Name": "MEETING_TIME", "Value": str(time)}
            ]
            print(f"پارامترهای ارسالی به API: {parameters}")
            
            try:
                result = send_template_sms(mobile, MEETING_TEMPLATE, parameters)
                print(f"نتیجه ارسال پیامک: {result}")
                if result:
                    print(f"پیامک با موفقیت به شماره {mobile} ارسال شد")
                else:
                    print(f"خطا در ارسال پیامک به شماره {mobile}")
            except Exception as e:
                print(f"خطا در فراخوانی API پیامک: {str(e)}")
        else:
            print(f"شماره موبایل خالی است")
    except Exception as e:
        print(f"خطای کلی در ارسال پیامک: {str(e)}")
        import traceback
        print(f"جزئیات خطا: {traceback.format_exc()}")

def send_meeting_created_sms(mobile, meeting_id, meeting_title, date, time):
    """
    ارسال پیامک برای ایجاد جلسه جدید
    """
    print(f"\n=== شروع ارسال پیامک ایجاد جلسه ===")
    send_meeting_sms(mobile, "ایجاد شد", meeting_id, meeting_title, date, time)

def send_meeting_cancelled_sms(mobile, meeting_id, meeting_title, date, time, reason):
    """
    ارسال پیامک برای لغو جلسه
    """
    print(f"\n=== شروع ارسال پیامک لغو جلسه ===")
    send_meeting_sms(mobile, "لغو شد", meeting_id, meeting_title, date, time)

def send_meeting_reminder_sms(mobile, meeting_id, meeting_title, date, time):
    """
    ارسال پیامک برای یادآوری جلسه
    """
    print(f"\n=== شروع ارسال پیامک یادآوری جلسه ===")
    send_meeting_sms(mobile, "یادآوری می‌شود", meeting_id, meeting_title, date, time)

def send_meeting_updated_sms(mobile, meeting_id, meeting_title, date, time):
    """
    ارسال پیامک برای بروزرسانی جلسه
    """
    print(f"\n=== شروع ارسال پیامک بروزرسانی جلسه ===")
    send_meeting_sms(mobile, "بروزرسانی شد", meeting_id, meeting_title, date, time)

def send_meeting_deleted_sms(mobile, meeting_id, meeting_title, date, time):
    """
    ارسال پیامک برای حذف جلسه
    """
    print(f"\n=== شروع ارسال پیامک حذف جلسه ===")
    send_meeting_sms(mobile, "حذف شد", meeting_id, meeting_title, date, time) 