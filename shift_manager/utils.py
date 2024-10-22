import datetime
from .models import InitialShiftSetup

SHIFT_PATTERN = [
    'روزکار اول', 'روزکار دوم', 'عصرکار اول', 'عصرکار دوم',
    'شب کار اول', 'شب کار دوم', 'OFF اول', 'OFF دوم'
]

def get_shift_for_date(input_date):
    try:
        initial_setup = InitialShiftSetup.objects.latest('start_date')
    except InitialShiftSetup.DoesNotExist:
        # ایجاد یک تنظیم پیش‌فرض
        initial_setup = InitialShiftSetup.objects.create(
            start_date=datetime.date(2024, 1, 1),  # تاریخ شروع پیش‌فرض
            group_A_shift='روزکار اول',
            group_B_shift='عصرکار اول',
            group_C_shift='شب کار اول',
            group_D_shift='OFF اول'
        )

    delta_days = (input_date - initial_setup.start_date).days
    shift_index = delta_days % len(SHIFT_PATTERN)

    shifts = {
        'A': SHIFT_PATTERN[(shift_index + 0) % len(SHIFT_PATTERN)],
        'B': SHIFT_PATTERN[(shift_index + 2) % len(SHIFT_PATTERN)],
        'C': SHIFT_PATTERN[(shift_index + 4) % len(SHIFT_PATTERN)],
        'D': SHIFT_PATTERN[(shift_index + 6) % len(SHIFT_PATTERN)],
    }

    return shifts