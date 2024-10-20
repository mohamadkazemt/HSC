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
        raise ValueError("No initial shift setup found. Please set an initial shift setup.")

    delta_days = (input_date - initial_setup.start_date).days
    shift_index = delta_days % len(SHIFT_PATTERN)

    shifts = {
        'A': SHIFT_PATTERN[(shift_index + 0) % len(SHIFT_PATTERN)],
        'B': SHIFT_PATTERN[(shift_index + 2) % len(SHIFT_PATTERN)],
        'C': SHIFT_PATTERN[(shift_index + 4) % len(SHIFT_PATTERN)],
        'D': SHIFT_PATTERN[(shift_index + 6) % len(SHIFT_PATTERN)],
    }

    return shifts
