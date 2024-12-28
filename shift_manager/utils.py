import datetime
from .models import InitialShiftSetup

SHIFT_PATTERN = [
    'روزکار اول', 'روزکار دوم', 'عصرکار اول', 'عصرکار دوم',
    'شب کار اول', 'شب کار دوم', 'OFF اول', 'OFF دوم'
]

def get_shift_for_date(input_date, user_profile=None):
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
    # اگر پروفایل کاربر ارسال شده باشه و گروه داشته باشه
    if user_profile and user_profile.group:
        group_shift_field = f"group_{user_profile.group}_shift"
        if hasattr(initial_setup, group_shift_field):
            initial_group_shift = getattr(initial_setup, group_shift_field)
            delta_days = (input_date - initial_setup.start_date).days
            group_shift = SHIFT_PATTERN[(SHIFT_PATTERN.index(initial_group_shift) + delta_days) % len(SHIFT_PATTERN)]

            return {
                'A': None if user_profile.group == "A" else  SHIFT_PATTERN[(SHIFT_PATTERN.index(initial_setup.group_A_shift) + delta_days) % len(SHIFT_PATTERN)],
                'B': None if user_profile.group == "B" else SHIFT_PATTERN[(SHIFT_PATTERN.index(initial_setup.group_B_shift) + delta_days) % len(SHIFT_PATTERN)],
                'C': None if user_profile.group == "C" else SHIFT_PATTERN[(SHIFT_PATTERN.index(initial_setup.group_C_shift) + delta_days) % len(SHIFT_PATTERN)],
                'D': None if user_profile.group == "D" else  SHIFT_PATTERN[(SHIFT_PATTERN.index(initial_setup.group_D_shift) + delta_days) % len(SHIFT_PATTERN)],
                'user_group_shift': group_shift
            }

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


def get_current_shift_and_group(user=None):
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
    if user and hasattr(user, 'userprofile'):
        shifts = get_shift_for_date(today, user.userprofile)
    else:
       shifts = get_shift_for_date(today)
    # یافتن گروه مرتبط با شیفت جاری
    group = None
    if user and hasattr(user, 'userprofile') and shifts.get('user_group_shift'):
       if shifts.get('user_group_shift') == current_shift:
          group = user.userprofile.group
    else:
       for grp, shift in shifts.items():
            if shift == current_shift:
                group = grp
                break
    return current_shift, group


def get_current_shift_and_group_without_user():
    """
    شناسایی شیفت جاری و گروه کاری مرتبط بدون در نظر گرفتن کاربر
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