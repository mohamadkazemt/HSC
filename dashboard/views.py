from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from dashboard.models import Notification
import jdatetime
from collections import Counter
from django.shortcuts import render
from anomalis.models import Anomaly

name = 'dashboard'


@login_required
def dashboard(request):
    unread_notifications_count = request.user.notifications.filter(is_read=False).count()
    notifications = Notification.objects.all().count()

    # سایر کدهای داشبورد
    is_admin_user = request.user.groups.filter(name='مدیر HSC').exists()
    is_followup_user = request.user.groups.filter(name='مسئول پیگیری').exists()
    is_safety_officer = request.user.groups.filter(name='افسر HSE').exists()

    print(unread_notifications_count)
    print(notifications)

    context = {
        'unread_notifications_count': unread_notifications_count,
        'is_admin_user': is_admin_user,
        'is_followup_user': is_followup_user,
        'is_safety_officer': is_safety_officer,
        'title': 'داشبورد',
    }

    return render(request, 'dashboard/dashboard.html', context)





@login_required
def notification_list(request):
    unread_notifications = request.user.notifications.filter(is_read=False)
    read_notifications = request.user.notifications.filter(is_read=True)

    return render(request, 'notification.html', {
        'unread_notifications': unread_notifications,
        'read_notifications': read_notifications,
    })


from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Notification


@login_required
def mark_notification_and_redirect(request, notification_id):
    # دریافت نوتیفیکیشن مربوطه
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)

    # علامت زدن به عنوان خوانده‌شده
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()

    # هدایت به URL مقصد نوتیفیکیشن
    return redirect(notification.url if notification.url else 'dashboard')





@login_required
def dashboard(request):
    # دریافت پارامترهای فیلتر از درخواست
    status_filter = request.GET.get('status', 'همه')
    priority_filter = request.GET.get('priority', 'همه')

    # فیلتر کردن داده‌های آنومالی بر اساس پارامترهای انتخاب شده
    anomalies = Anomaly.objects.all()

    if status_filter == 'ایمن':
        anomalies = anomalies.filter(action=True)
    elif status_filter == 'نا ایمن':
        anomalies = anomalies.filter(action=False)

    if priority_filter != 'همه':
        anomalies = anomalies.filter(priority__priority=priority_filter)

    # تبدیل تاریخ‌ها به ماه و سال شمسی و شمارش تعداد آنومالی‌ها
    anomaly_dates = [
        jdatetime.datetime.fromgregorian(datetime=anomaly.created_at).strftime("%Y-%m")
        for anomaly in anomalies
    ]
    anomaly_counts = Counter(anomaly_dates)
    months = list(anomaly_counts.keys())
    counts = list(anomaly_counts.values())

    context = {
        'months': months,  # ماه‌های شمسی
        'counts': counts,  # تعداد آنومالی‌ها در هر ماه
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'title': 'داشبورد',
    }

    return render(request, 'dashboard/dashboard.html', context)
