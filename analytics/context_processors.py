from .utils import get_anomaly_stats_all_users
from .views import get_anomaly_stats

def anomaly_stats_context(request):
    # چک می‌کنیم که آیا کاربر لاگین کرده است یا خیر
    if request.user.is_authenticated:
        # اگر کاربر لاگین کرده باشد، آمار برای کاربر خاص را می‌گیریم
        user_stats = get_anomaly_stats(request.user)
    else:
        # در غیر این صورت، مقادیر پیش‌فرض برای آمار کاربر لاگین نشده
        user_stats = {
            'total_anomalies': 0,
            'secured_anomalies': 0,
            'unsafe_anomalies': 0,
            'high_priority_anomalies': 0,
        }

    # محاسبه آمار برای تمام کاربران در سال شمسی جاری
    all_users_stats = get_anomaly_stats_all_users()

    # آمار مربوط به کاربر لاگین شده و آمار کل برای همه کاربران را به قالب ارسال می‌کنیم
    return {
        'user_anomaly_stats': user_stats,
        'all_users_anomaly_stats': all_users_stats
    }
