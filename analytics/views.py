from django.shortcuts import render

from analytics.utils import get_anomaly_stats
from anomalis.models import Anomaly
from django.contrib.auth.decorators import login_required


@login_required
@login_required
def anomaly_analytics(request):
    user = request.user
    stats = get_anomaly_stats(user)  # استفاده از تابع مشترک برای محاسبه آمار

    return render(request, 'dashboard/dashboard.html', {'stats': stats})
