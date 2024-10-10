from anomalis.models import Anomaly


def get_anomaly_stats(user):
    total_anomalies = Anomaly.objects.filter(followup=user).count()
    secured_anomalies = Anomaly.objects.filter(followup=user, action=True).count()
    unsafe_anomalies = Anomaly.objects.filter(followup=user, action=False).count()
    high_priority_anomalies = Anomaly.objects.filter(followup=user, priority__priority="زیاد").count()

    return {
        'total_anomalies': total_anomalies,
        'secured_anomalies': secured_anomalies,
        'unsafe_anomalies': unsafe_anomalies,
        'high_priority_anomalies': high_priority_anomalies,
    }
