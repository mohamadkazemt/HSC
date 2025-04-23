import datetime
from django.utils import timezone
from shift_manager.utils import get_shift_for_date

def get_shift_for_date_and_time(date, time, work_group):
    """
    Determines the shift based on the date, time, and work group.
    For night shifts, it checks if the time is between 6 PM and 6 AM to assign the correct shift.
    """
    if 18 <= time.hour <= 23 or 0 <= time.hour < 6:
        # If the time is between 6 PM and 6 AM, consider it as the night shift
        shift_info = get_shift_for_date(date)
        return shift_info.get(work_group)
    else:
        # For other shifts, use the default logic
        shift_info = get_shift_for_date(date)
        return shift_info.get(work_group) 