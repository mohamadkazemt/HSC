from django.shortcuts import render
import datetime
from shift_manager.utils import get_shift_for_date

def shift_calendar_view(request):
    # گرفتن تاریخ امروز
    today = datetime.date.today()

    # محاسبه شیفت‌ها برای ۳۰ روز آینده
    shift_data = {}
    for i in range(30):
        date = today + datetime.timedelta(days=i)
        shifts = get_shift_for_date(date)
        shift_data[date.isoformat()] = shifts

    context = {
        'shift_data': shift_data,
    }

    return render(request, 'shift_manager/shift_calendar.html', context)
