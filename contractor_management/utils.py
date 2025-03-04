# contractor_management/utils.py

from shift_manager.utils import get_shift_for_date, SHIFT_PATTERN
import datetime


def get_current_user_shift_and_group(user):
    """
    شناسایی شیفت جاری یا شیفت بعدی مرتبط با کاربر
    """
    now = datetime.datetime.now()
    today = now.date()
    current_hour = now.hour
    current_minute = now.minute

    if user and hasattr(user, 'userprofile') and user.userprofile.group:
        shifts = get_shift_for_date(today, user.userprofile)
        user_group = user.userprofile.group
        user_shift = shifts.get('user_group_shift')
        if user_shift:
             shift_index = SHIFT_PATTERN.index(user_shift)
             next_shift_index = (shift_index + 1) % len(SHIFT_PATTERN)
             next_shift = SHIFT_PATTERN[next_shift_index]
             
             # تعیین ساعت‌های شیفت
             if user_shift == 'روزکار اول':
                  shift_start_hour = 7
                  shift_end_hour = 15
             elif user_shift == 'عصرکار اول':
                  shift_start_hour = 15
                  shift_end_hour = 23
             elif user_shift == 'شب کار اول':
                  shift_start_hour = 23
                  shift_end_hour = 7  # ساعت پایان شیفت شب در روز بعد
             elif user_shift == 'روزکار دوم':
                  shift_start_hour = 7
                  shift_end_hour = 15
             elif user_shift == 'عصرکار دوم':
                  shift_start_hour = 15
                  shift_end_hour = 23
             elif user_shift == 'شب کار دوم':
                  shift_start_hour = 23
                  shift_end_hour = 7  # ساعت پایان شیفت شب در روز بعد
             else: # برای شیفت های آف
                 return None, None

             # بررسی زمان فعلی در محدوده شیفت
             if 'شب کار' in user_shift:
                 # برای شیفت شب، باید بررسی کنیم آیا ساعت فعلی بین 23 تا 24 است یا بین 0 تا 7
                 if (current_hour >= shift_start_hour) or (current_hour < shift_end_hour):
                     return user_shift, user_group
             else:
                 # برای شیفت‌های روز و عصر
                 if shift_start_hour <= current_hour < shift_end_hour:
                     return user_shift, user_group

    return None, None
