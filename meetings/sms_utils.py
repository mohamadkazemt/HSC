import logging
from datetime import date as gregorian_date, datetime

import jdatetime

from core.sms_service import send_template_sms

logger = logging.getLogger(__name__)

MEETING_TEMPLATE = 226785


def format_jalali_date(value):
    """Return a stable YYYY/MM/DD Jalali date for every SMS entry point."""
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, gregorian_date):
        jalali = jdatetime.date.fromgregorian(date=value)
        return f'{jalali.year:04d}/{jalali.month:02d}/{jalali.day:02d}'
    if isinstance(value, jdatetime.datetime):
        value = value.date()
    if isinstance(value, jdatetime.date):
        return f'{value.year:04d}/{value.month:02d}/{value.day:02d}'
    if isinstance(value, str):
        normalized = value.strip().translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789'))
        normalized = normalized.replace('/', '-')
        try:
            year, month, day = map(int, normalized.split('-'))
            if 1300 <= year <= 1500:
                return f'{year:04d}/{month:02d}/{day:02d}'
            parsed = gregorian_date(year, month, day)
            jalali = jdatetime.date.fromgregorian(date=parsed)
            return f'{jalali.year:04d}/{jalali.month:02d}/{jalali.day:02d}'
        except (TypeError, ValueError):
            logger.warning('Invalid meeting SMS date value: %r', value)
    raise ValueError(f'Invalid meeting date: {value!r}')


def format_meeting_time(value):
    if hasattr(value, 'strftime'):
        return value.strftime('%H:%M')
    return str(value)[:5]


def send_meeting_sms(mobile, status, meeting_id, meeting_title, date, time):
    """Send a meeting template SMS with normalized Jalali date and time."""
    if not mobile:
        logger.warning('Meeting %s SMS skipped because mobile is empty', meeting_id)
        return False

    try:
        parameters = [
            {'Name': 'STATUS', 'Value': status},
            {'Name': 'MEETING_TITLE', 'Value': meeting_title},
            {'Name': 'MEETING_DATE', 'Value': format_jalali_date(date)},
            {'Name': 'MEETING_TIME', 'Value': format_meeting_time(time)},
        ]
        return send_template_sms(mobile, MEETING_TEMPLATE, parameters)
    except Exception:
        logger.exception('Could not send meeting %s SMS to %s', meeting_id, mobile)
        return False


def send_meeting_created_sms(mobile, meeting_id, meeting_title, date, time):
    return send_meeting_sms(mobile, 'ایجاد شد', meeting_id, meeting_title, date, time)


def send_meeting_cancelled_sms(mobile, meeting_id, meeting_title, date, time, reason):
    return send_meeting_sms(mobile, 'لغو شد', meeting_id, meeting_title, date, time)


def send_meeting_reminder_sms(mobile, meeting_id, meeting_title, date, time):
    return send_meeting_sms(mobile, 'یادآوری می‌شود', meeting_id, meeting_title, date, time)


def send_meeting_updated_sms(mobile, meeting_id, meeting_title, date, time):
    return send_meeting_sms(mobile, 'بروزرسانی شد', meeting_id, meeting_title, date, time)


def send_meeting_deleted_sms(mobile, meeting_id, meeting_title, date, time):
    return send_meeting_sms(mobile, 'حذف شد', meeting_id, meeting_title, date, time)