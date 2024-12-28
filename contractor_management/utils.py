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
             # تبدیل ساعت شیفت به بازه زمانی
             if user_shift == 'روزکار اول':
                  shift_start_hour = 7
                  shift_end_hour = 14
             elif user_shift == 'عصرکار اول':
                  shift_start_hour = 15
                  shift_end_hour = 22
             elif user_shift == 'شب کار اول':
                 shift_start_hour = 23
                 shift_end_hour = 6 if next_shift != 'روزکار اول' else 7
             elif user_shift == 'روزکار دوم':
                  shift_start_hour = 7
                  shift_end_hour = 14
             elif user_shift == 'عصرکار دوم':
                  shift_start_hour = 15
                  shift_end_hour = 22
             elif user_shift == 'شب کار دوم':
                 shift_start_hour = 23
                 shift_end_hour = 6 if next_shift != 'روزکار اول' else 7
             else: # برای شیفت های آف
                 return None, None
             # بررسی اینکه ساعت فعلی بین شیفت و شیفت بعدی هست یا نه
             shift_end_hour_extended = (shift_end_hour + 8) % 24
             if shift_start_hour <= shift_end_hour: # شیفت روزکار و عصر کار
                if (shift_start_hour <= current_hour < shift_end_hour) or (shift_end_hour <= current_hour < shift_end_hour_extended if shift_end_hour_extended > shift_end_hour else current_hour < shift_end_hour_extended):
                        return user_shift, user_group
             else: # شیفت شب کار
                  if (shift_start_hour <= current_hour or current_hour < shift_end_hour) or (shift_end_hour <= current_hour or current_hour < shift_end_hour_extended if shift_end_hour_extended > shift_end_hour else current_hour < shift_end_hour_extended):
                      return user_shift, user_group
    return None, None