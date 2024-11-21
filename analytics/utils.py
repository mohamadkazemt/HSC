from anomalis.models import Anomaly
from accounts.models import UserProfile
import jdatetime
from datetime import datetime

def get_anomaly_stats(user):
    try:
        # دریافت UserProfile مرتبط با کاربر
        user_profile = UserProfile.objects.get(user=user)

        # استفاده از user_profile برای فیلتر کردن آنومالی‌ها
        total_anomalies = Anomaly.objects.filter(followup=user_profile).count()
        secured_anomalies = Anomaly.objects.filter(followup=user_profile, action=True).count()
        unsafe_anomalies = Anomaly.objects.filter(followup=user_profile, action=False).count()
        high_priority_anomalies = Anomaly.objects.filter(followup=user_profile, priority__priority="زیاد( High)").count()

        return {
            'total_anomalies': total_anomalies,
            'secured_anomalies': secured_anomalies,
            'unsafe_anomalies': unsafe_anomalies,
            'high_priority_anomalies': high_priority_anomalies,
        }

    except UserProfile.DoesNotExist:
        # در صورتی که پروفایل پیدا نشود این بخش اجرا خواهد شد
        return {
            'total_anomalies': 0,
            'secured_anomalies': 0,
            'unsafe_anomalies': 0,
            'high_priority_anomalies': 0,
        }






def get_anomaly_stats_all_users():
    current_year_shamsi = jdatetime.datetime.now().year
    start_of_shamsi_year = jdatetime.datetime(current_year_shamsi, 1, 1).togregorian()
    end_of_shamsi_year = jdatetime.datetime(current_year_shamsi, 12, 29).togregorian()
    total_anomalies_year = Anomaly.objects.filter(created_at__range=(start_of_shamsi_year, end_of_shamsi_year)).count()
    secured_anomalies_year = Anomaly.objects.filter(action=True, created_at__range=(start_of_shamsi_year, end_of_shamsi_year)).count()
    unsafe_anomalies_year = Anomaly.objects.filter(action=False, created_at__range=(start_of_shamsi_year, end_of_shamsi_year)).count()
    high_priority_anomalies_year = Anomaly.objects.filter(priority__priority="زیاد", created_at__range=(start_of_shamsi_year, end_of_shamsi_year)).count()

    return {
        'total_anomalies_year': total_anomalies_year,
        'secured_anomalies_year': secured_anomalies_year,
        'unsafe_anomalies_year': unsafe_anomalies_year,
        'high_priority_anomalies_year': high_priority_anomalies_year,
    }
