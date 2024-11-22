import datetime
from .models import InitialShiftSetup

SHIFT_PATTERN = [
    'روزکار اول', 'روزکار دوم', 'عصرکار اول', 'عصرکار دوم',
    'شب کار اول', 'شب کار دوم', 'OFF اول', 'OFF دوم'
]

def get_shift_for_date(input_date):
    try:
        # گرفتن آخرین تنظیمات اولیه شیفت‌ها
        initial_setup = InitialShiftSetup.objects.latest('start_date')
    except InitialShiftSetup.DoesNotExist:
        # ایجاد یک تنظیم پیش‌فرض در صورت نبود رکورد
        initial_setup = InitialShiftSetup.objects.create(
            start_date=datetime.date(2024, 1, 1),  # تاریخ شروع پیش‌فرض
            group_A_shift='روزکار اول',
            group_B_shift='عصرکار اول',
            group_C_shift='شب کار اول',
            group_D_shift='OFF اول'
        )

    # محاسبه تعداد روزهایی که از تاریخ شروع گذشته است
    delta_days = (input_date - initial_setup.start_date).days

    # محاسبه شیفت‌ها برای هر گروه به صورت جداگانه با استفاده از الگوی شیفت‌ها
    shifts = {
        'A': SHIFT_PATTERN[(SHIFT_PATTERN.index(initial_setup.group_A_shift) + delta_days) % len(SHIFT_PATTERN)],
        'B': SHIFT_PATTERN[(SHIFT_PATTERN.index(initial_setup.group_B_shift) + delta_days) % len(SHIFT_PATTERN)],
        'C': SHIFT_PATTERN[(SHIFT_PATTERN.index(initial_setup.group_C_shift) + delta_days) % len(SHIFT_PATTERN)],
        'D': SHIFT_PATTERN[(SHIFT_PATTERN.index(initial_setup.group_D_shift) + delta_days) % len(SHIFT_PATTERN)],
    }

    return shifts



def get_current_shift_and_group():
    """
    شناسایی شیفت جاری و گروه کاری مرتبط
    """
    # دریافت تاریخ و ساعت فعلی
    now = datetime.datetime.now()
    today = now.date()
    current_hour = now.hour
    current_minute = now.minute

    # تعیین شیفت جاری بر اساس ساعت و دقیقه
    if (current_hour == 6 and current_minute >= 45) or (7 <= current_hour < 14) or (current_hour == 14 and current_minute < 45):
        current_shift = 'روزکار اول'
    elif (current_hour == 14 and current_minute >= 45) or (15 <= current_hour < 22) or (current_hour == 22 and current_minute < 45):
        current_shift = 'عصرکار اول'
    elif (current_hour == 22 and current_minute >= 45) or (current_hour < 6) or (current_hour == 6 and current_minute < 45):
        current_shift = 'شب کار اول'
    else:
        return None, None  # اگر ساعت نامعتبر باشد

    # گرفتن شیفت‌ها برای امروز
    shifts = get_shift_for_date(today)

    # یافتن گروه مرتبط با شیفت جاری
    group = None
    for grp, shift in shifts.items():
        if shift == current_shift:
            group = grp
            break

    return current_shift, group

