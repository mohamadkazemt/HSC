import logging
import jdatetime
from core.sms_service import send_template_sms

logger = logging.getLogger(__name__)

# شناسه قالب پیامک جلسات
MEETING_TEMPLATE = 226785  # قالب پیامک برای تمام عملیات جلسات

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