import datetime
from django.utils import timezone
from .models import InitialShiftSetup
from accounts.models import UserProfile  # Import UserProfile

SHIFT_PATTERN = [
    'روزکار اول', 'روزکار دوم', 'عصرکار اول', 'عصرکار دوم',
    'شب کار اول', 'شب کار دوم', 'OFF اول', 'OFF دوم'
]

def get_shift_for_date(input_date, user_profile=None):
    """
    Calculates the shift assignments for each group (A, B, C, D) on a given date,
    optionally considering a specific user's profile to return their individual shift.
    """
    try:
        # Get the latest initial shift setup
        initial_setup = InitialShiftSetup.objects.latest('start_date')
    except InitialShiftSetup.DoesNotExist:
        # Create a default setup if none exists
        initial_setup = InitialShiftSetup.objects.create(
            start_date=datetime.date(2024, 1, 1),
            group_A_shift='روزکار اول',
            group_B_shift='عصرکار اول',
            group_C_shift='شب کار اول',
            group_D_shift='OFF اول'
        )

    delta_days = (input_date - initial_setup.start_date).days

    # Calculate shift index offset based on the number of days since the start date
    shift_offset = delta_days % len(SHIFT_PATTERN)

    # Helper function to calculate the shift for a given group
    def calculate_shift(group_shift):
        return SHIFT_PATTERN[(SHIFT_PATTERN.index(group_shift) + shift_offset) % len(SHIFT_PATTERN)]

    # If a user profile is provided, return the shift assignment for that user's group
    if user_profile and user_profile.group:
        user_group = user_profile.group
        group_shift_field = f"group_{user_group}_shift"

        if hasattr(initial_setup, group_shift_field):
            initial_group_shift = getattr(initial_setup, group_shift_field)
            user_group_shift = calculate_shift(initial_group_shift)

            # Return individual shifts for all groups except the user's
            shifts = {
                group: calculate_shift(getattr(initial_setup, f"group_{group}_shift")) if group != user_group else None
                for group in ['A', 'B', 'C', 'D']
            }

            return {
                **shifts,
                'user_group_shift': user_group_shift,
                'user_group': user_group,
            }
        else:
             return {
                'A': None,
                'B': None,
                'C': None,
                'D': None,
                'user_group_shift': None,
                'user_group': user_group,
            }


    # If no user profile is provided, return shift assignments for all groups
    shifts = {
        'A': calculate_shift(initial_setup.group_A_shift),
        'B': calculate_shift(initial_setup.group_B_shift),
        'C': calculate_shift(initial_setup.group_C_shift),
        'D': calculate_shift(initial_setup.group_D_shift),
    }

    return shifts


def get_current_shift_and_group(user=None):
    """
    Identifies the current shift and associated work group. If a user is provided,
    it attempts to determine their specific group and shift using get_shift_for_date.
    """
    now = timezone.now()  # Use timezone.now() for timezone-aware datetime
    current_time = now.time()
    today = now.date()

    # Determine shift based on time ranges
    if datetime.time(6, 45) <= current_time < datetime.time(14, 45):
        current_shift = 'روزکار اول'
    elif datetime.time(14, 45) <= current_time < datetime.time(22, 45):
        current_shift = 'عصرکار اول'
    else:  # Covers 22:45 to 6:45
        current_shift = 'شب کار اول'

    # Determine shift and group based on user profile or general date
    if user and hasattr(user, 'userprofile'):
        user_profile = user.userprofile
        shifts = get_shift_for_date(today, user_profile)
        user_group_shift = shifts.get('user_group_shift')
        user_group = shifts.get('user_group')  # Use user_group here

        if user_group_shift:
            return user_group_shift, user_group  # Use user_group here
        else:
            return None, user_group  # Use user_group here
    else:
        shifts = get_shift_for_date(today)
        group = next((grp for grp, shift in shifts.items() if shift == current_shift), None)
        return current_shift, group


def get_active_groups_for_current_shift():
    """
    Returns a list of all active groups (A, B, C, D) that are currently working
    based on the current shift time.
    
    Returns:
        tuple: (current_shift_name, list_of_active_groups)
        Example: ('روزکار اول', ['A', 'B'])
    """
    now = timezone.now()
    current_time = now.time()
    today = now.date()

    # Determine current shift based on time ranges
    if datetime.time(6, 45) <= current_time < datetime.time(14, 45):
        current_shift = 'روزکار اول'
    elif datetime.time(14, 45) <= current_time < datetime.time(22, 45):
        current_shift = 'عصرکار اول'
    else:  # Covers 22:45 to 6:45
        current_shift = 'شب کار اول'

    # Get shifts for all groups today
    shifts = get_shift_for_date(today)
    
    # Find all groups that match the current shift
    # Note: We need to check both 'first' and 'second' variations
    # Also, 'OFF' shifts should not be considered as active
    active_groups = []
    shift_variations = [
        current_shift,
        current_shift.replace('اول', 'دوم') if 'اول' in current_shift else current_shift.replace('دوم', 'اول')
    ]
    
    for group, group_shift in shifts.items():
        # Skip OFF shifts - they are not active working shifts
        if group_shift and 'OFF' not in group_shift and group_shift in shift_variations:
            active_groups.append(group)
    
    return current_shift, active_groups