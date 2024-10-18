from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from dashboard.models import Notification



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



from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def notification_list(request):
    unread_notifications = request.user.notifications.filter(is_read=False)
    read_notifications = request.user.notifications.filter(is_read=True)

    return render(request, 'notification.html', {
        'unread_notifications': unread_notifications,
        'read_notifications': read_notifications,
    })


@login_required
def mark_notifications_as_read(request):
    notifications = request.user.notifications.filter(is_read=False)
    notifications.update(is_read=True)
    return redirect('dashboard')
