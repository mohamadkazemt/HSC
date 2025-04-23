from django.shortcuts import render
import datetime
from django.utils import timezone
from shift_manager.utils import get_shift_for_date
import jdatetime
import logging
import calendar
from django.template.defaultfilters import date

# تنظیمات لاگینگ
logger = logging.getLogger(__name__)


def shift_calendar_view(request):
    today = jdatetime.datetime.now()
    year = request.GET.get('year', today.year)
    month = request.GET.get('month', today.month)

    # اسامی ماه‌های شمسی
    months = {
        1: 'فروردین',
        2: 'اردیبهشت',
        3: 'خرداد',
        4: 'تیر',
        5: 'مرداد',
        6: 'شهریور',
        7: 'مهر',
        8: 'آبان',
        9: 'آذر',
        10: 'دی',
        11: 'بهمن',
        12: 'اسفند'
    }

    try:
        year = int(year)
        month = int(month)

        if year < 1 or month < 1 or month > 12:
            logger.error(f"Invalid year or month: year={year}, month={month}")
            raise ValueError("Year or month is out of valid range.")

        # محاسبه روز آخر ماه شمسی
        if month <= 6:
            last_day = 31
        elif month <= 11:
            last_day = 30
        else:  # month == 12
            if jdatetime.date(year, month, 1).isleap():
                last_day = 30
            else:
                last_day = 29

        # تولید لیست تاریخ‌های شمسی برای ماه انتخاب شده
        calendar_data = []
        first_day_of_month = jdatetime.date(year, month, 1)
        weekday = first_day_of_month.weekday()  # 0: شنبه, 1: یکشنبه, ..., 6: جمعه

        # اضافه کردن روزهای خالی برای روزهای قبل از اول ماه
        first_week = [None] * weekday

        # اضافه کردن روزهای ماه
        days_in_month = []
        for day in range(1, last_day + 1):
            days_in_month.append(jdatetime.date(year, month, day))

        # ترکیب روزهای خالی و روزهای ماه
        first_week.extend(days_in_month[:7 - weekday])
        calendar_data.append(first_week)

        # پر کردن بقیه هفته‌ها
        remaining_days = days_in_month[7 - weekday:]
        while remaining_days:
            week = remaining_days[:7]
            calendar_data.append(week)
            remaining_days = remaining_days[7:]

        # محاسبه شیفت‌ها برای کل روزهای ماه
        shift_data = {}
        for week in calendar_data:
            for j_date in week:
                if j_date:
                    g_date = j_date.togregorian()
                    shifts = get_shift_for_date(g_date)
                    # تبدیل تاریخ به فرمت مناسب
                    formatted_date = j_date.strftime('%Y-%m-%d')
                    shift_data[formatted_date] = shifts

    except ValueError as e:
        logger.error(f"Error processing date: {e}")
        return render(request, 'shift_manager/error.html', {'error': 'تاریخ نامعتبر'})

    context = {
        'year': year,
        'month': month,
        'months': months,
        'shift_data': shift_data,
        'calendar': calendar_data,
    }

    return render(request, 'shift_manager/shift_calendar.html', context)