from .views import get_anomaly_stats  # یا از utils.py وارد کنید

def anomaly_stats_context(request):
    if request.user.is_authenticated:
        stats = get_anomaly_stats(request.user)
    else:
        stats = {
            'total_anomalies': 0,
            'secured_anomalies': 0,
            'unsafe_anomalies': 0,
            'high_priority_anomalies': 0,
        }
    return {'anomaly_stats': stats}
