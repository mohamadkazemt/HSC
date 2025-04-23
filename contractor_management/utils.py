# contractor_management/utils.py

from shift_manager.utils import get_shift_for_date, SHIFT_PATTERN
import datetime
import logging

logger = logging.getLogger(__name__)


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
        
        # اگر شیفت تشخیص داده شد، آن را برگردان
        if user_shift:
            logger.info(f"شیفت کاری تشخیص داده شده: {user_shift} برای گروه {user_group}")
            return user_shift, user_group
        
        # اگر شیفت تشخیص داده نشد، از تابع get_current_shift_and_group استفاده کنیم
        from shift_manager.utils import get_current_shift_and_group as get_shift
        current_shift, current_group = get_shift(user)
        
        if current_shift and current_group:
            logger.info(f"شیفت کاری از تابع get_current_shift_and_group: {current_shift} برای گروه {current_group}")
            return current_shift, current_group
        
        # اگر هنوز هم شیفت تشخیص داده نشد، حداقل گروه را برگردان
        logger.info(f"فقط گروه کاری برگردانده می‌شود: {user_group}")
        return None, user_group

    return None, None
