from .utils import get_shift_for_date
import datetime
from .models import InitialShiftSetup


def shift_context_processor(request):
    try:
        # بررسی اینکه رکورد اولیه وجود دارد
        initial_setup = InitialShiftSetup.objects.latest('start_date')
        today = datetime.date.today()
        shifts = get_shift_for_date(today)
        return {'shifts': shifts}
    except InitialShiftSetup.DoesNotExist:
        # اگر هیچ رکوردی وجود نداشت، برگرداندن یک مقدار خالی
        return {'shifts': None}




def shift_data_processor(request):
    # محاسبه شیفت‌ها برای ۳۰ روز آینده
    today = datetime.date.today()
    shift_data = {}
    for i in range(30):
        date = today + datetime.timedelta(days=i)
        shifts = get_shift_for_date(date)
        shift_data[date.isoformat()] = shifts

    return {
        'shift_data': shift_data,
    }
