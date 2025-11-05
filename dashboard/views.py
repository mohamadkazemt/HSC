# dashboard/views.py
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from dashboard.models import Notification
import jdatetime
from collections import Counter
from django.shortcuts import render
from anomalis.models import Anomaly
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import UserActivity
from permissions.utils import get_all_views_with_labels
from permissions.models import UserPermission, PartPermission, SectionPermission, PositionPermission, UnitGroupPermission
from accounts.models import UnitGroup, UserProfile, DriverLicense
from django.contrib import messages
from django.http import JsonResponse

name = 'dashboard'


@login_required
def dashboard(request):
    # بررسی نقش کاربر و وضعیت گواهینامه
    is_operator = any('اپراتور' in group.name for group in request.user.groups.all())
    driver_license = None
    license_warning = None
    
    if is_operator:
        try:
            driver_license = DriverLicense.objects.get(user=request.user)
            if not driver_license.is_complete():
                license_warning = "لطفاً اطلاعات گواهینامه خود را تکمیل کنید."
        except DriverLicense.DoesNotExist:
            license_warning = "لطفاً اطلاعات گواهینامه خود را تکمیل کنید."

    # دریافت اعلان‌های خوانده نشده
    unread_notifications_count = request.user.notifications.filter(is_read=False).count()
    
    # ============= کارتابل مرخصی‌ها =============
    from leave_reports.models import ShiftReport, ApprovalHierarchy
    from django.db.models import Q
    
    # درخواست‌های منتظر تأیید جایگزین
    pending_replacement_approvals = ShiftReport.objects.filter(
        replacement_person=request.user,
        status='pending_replacement'
    ).select_related('user', 'user__userprofile').order_by('-created_at')[:5]
    
    # درخواست‌های منتظر تأیید مدیر
    pending_manager_approvals = []
    if hasattr(request.user, 'userprofile'):
        managed_sections = ApprovalHierarchy.objects.filter(
            approver=request.user.userprofile
        ).values_list('section_id', flat=True)
        
        managed_parts = ApprovalHierarchy.objects.filter(
            approver=request.user.userprofile
        ).values_list('part_id', flat=True)
        
        pending_manager_approvals = ShiftReport.objects.filter(
            Q(user__userprofile__section_id__in=managed_sections) |
            Q(user__userprofile__part_id__in=managed_parts),
            status='pending_approval'
        ).select_related('user', 'user__userprofile').order_by('-created_at')[:5]
    
    # دریافت ۵ اعلان اخیر برای نمایش در داشبورد
    recent_notifications = request.user.notifications.all().order_by('-created_at')[:5]
    
    # دریافت فعالیت‌های اخیر کاربر
    recent_activities = UserActivity.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # دریافت دسترسی‌های مستقیم کاربر
    user_permissions = UserPermission.objects.filter(user=request.user)
    
    # دریافت دسترسی‌های کاربر بر اساس قسمت
    part_permissions = []
    if hasattr(request.user, 'userprofile') and request.user.userprofile.part:
        part_permissions = PartPermission.objects.filter(part=request.user.userprofile.part)
    
    # دریافت دسترسی‌های کاربر بر اساس بخش
    section_permissions = []
    if hasattr(request.user, 'userprofile') and request.user.userprofile.section:
        section_permissions = SectionPermission.objects.filter(section=request.user.userprofile.section)
    
    # دریافت دسترسی‌های کاربر بر اساس سمت
    position_permissions = []
    if hasattr(request.user, 'userprofile') and request.user.userprofile.position:
        position_permissions = PositionPermission.objects.filter(position=request.user.userprofile.position)
    
    # دریافت دسترسی‌های کاربر بر اساس گروه
    unit_group_permissions = []
    if hasattr(request.user, 'userprofile') and request.user.userprofile.group:
        # ابتدا سعی می‌کنیم گروه را بر اساس نام پیدا کنیم
        try:
            unit_group = UnitGroup.objects.get(name=request.user.userprofile.group)
            unit_group_permissions = UnitGroupPermission.objects.filter(unit_group=unit_group)
        except (UnitGroup.DoesNotExist, ValueError):
            # اگر گروه پیدا نشد یا خطای دیگری رخ داد، لیست خالی برمی‌گردانیم
            unit_group_permissions = []
    
    # دریافت لیبل‌های ویوها
    views_with_labels = get_all_views_with_labels()
    view_labels = {view['name']: view['label'] for view in views_with_labels}
    
    # ترکیب همه دسترسی‌ها
    all_permissions = []
    
    # افزودن دسترسی‌های مستقیم کاربر
    for perm in user_permissions:
        all_permissions.append({
            'type': 'کاربر',
            'view_name': perm.view_name,
            'view_label': view_labels.get(perm.view_name, perm.view_name),
            'can_view': perm.can_view,
            'can_add': perm.can_add,
            'can_edit': perm.can_edit,
            'can_delete': perm.can_delete,
        })
    
    # افزودن دسترسی‌های قسمت
    for perm in part_permissions:
        all_permissions.append({
            'type': 'قسمت',
            'view_name': perm.view_name,
            'view_label': view_labels.get(perm.view_name, perm.view_name),
            'can_view': perm.can_view,
            'can_add': perm.can_add,
            'can_edit': perm.can_edit,
            'can_delete': perm.can_delete,
        })
    
    # افزودن دسترسی‌های بخش
    for perm in section_permissions:
        all_permissions.append({
            'type': 'بخش',
            'view_name': perm.view_name,
            'view_label': view_labels.get(perm.view_name, perm.view_name),
            'can_view': perm.can_view,
            'can_add': perm.can_add,
            'can_edit': perm.can_edit,
            'can_delete': perm.can_delete,
        })
    
    # افزودن دسترسی‌های سمت
    for perm in position_permissions:
        all_permissions.append({
            'type': 'سمت',
            'view_name': perm.view_name,
            'view_label': view_labels.get(perm.view_name, perm.view_name),
            'can_view': perm.can_view,
            'can_add': perm.can_add,
            'can_edit': perm.can_edit,
            'can_delete': perm.can_delete,
        })
    
    # افزودن دسترسی‌های گروه
    for perm in unit_group_permissions:
        all_permissions.append({
            'type': 'گروه',
            'view_name': perm.view_name,
            'view_label': view_labels.get(perm.view_name, perm.view_name),
            'can_view': perm.can_view,
            'can_add': perm.can_add,
            'can_edit': perm.can_edit,
            'can_delete': perm.can_delete,
        })
    
    # حذف دسترسی‌های تکراری (بر اساس view_name)
    unique_permissions = {}
    for perm in all_permissions:
        view_name = perm['view_name']
        if view_name not in unique_permissions:
            unique_permissions[view_name] = perm
    
    # تبدیل به لیست
    user_access_permissions_list = list(unique_permissions.values())
    
    # صفحه‌بندی دسترسی‌ها
    page = request.GET.get('page', 1)
    paginator = Paginator(user_access_permissions_list, 5)  # 5 دسترسی در هر صفحه
    
    try:
        user_access_permissions = paginator.page(page)
    except PageNotAnInteger:
        user_access_permissions = paginator.page(1)
    except EmptyPage:
        user_access_permissions = paginator.page(paginator.num_pages)
    
    # آمار موارد ثبت شده (اگر مدل Anomaly وجود دارد)
    stats = None
    if hasattr(request.user, 'anomalies'):
        total_anomalies = request.user.anomalies.count()
        completed_anomalies = request.user.anomalies.filter(status='completed').count()
        in_progress_anomalies = request.user.anomalies.filter(status='in_progress').count()
        
        stats = {
            'total_anomalies': total_anomalies,
            'completed_anomalies': completed_anomalies,
            'in_progress_anomalies': in_progress_anomalies,
        }

    # برای اطمینان از وجود داده‌ها، یک لاگ اضافه کنید
    print(f"Recent activities count: {recent_activities.count()}")
    
    context = {
        'unread_notifications_count': unread_notifications_count,
        'recent_notifications': recent_notifications,
        'recent_activities': recent_activities,  # اضافه کردن فعالیت‌های اخیر
        'user_access_permissions': user_access_permissions,
        'stats': stats,
        'title': 'داشبورد',
        'license_warning': license_warning,
        'driver_license': driver_license,
        # کارتابل مرخصی‌ها
        'pending_replacement_approvals': pending_replacement_approvals,
        'pending_manager_approvals': pending_manager_approvals,
    }

    return render(request, 'dashboard/dashboard.html', context)


@login_required
def notification_list(request):
    # دریافت تمام اعلان های خوانده نشده و مرتب کردن بر اساس created_at (جدیدترین اول)
    unread_notifications_list = request.user.notifications.filter(is_read=False).order_by('-created_at')

    # دریافت تمام اعلان های خوانده شده و مرتب کردن بر اساس created_at (جدیدترین اول)
    read_notifications_list = request.user.notifications.filter(is_read=True).order_by('-created_at')

    # صفحه بندی برای اعلان های خوانده نشده
    page_unread = request.GET.get('page_unread', 1)
    paginator_unread = Paginator(unread_notifications_list, 5)  # 5 اعلان در هر صفحه
    try:
        unread_notifications = paginator_unread.get_page(page_unread)
    except PageNotAnInteger:
        unread_notifications = paginator_unread.get_page(1)
    except EmptyPage:
        unread_notifications = paginator_unread.get_page(paginator_unread.num_pages)

    # صفحه بندی برای اعلان های خوانده شده
    page_read = request.GET.get('page_read', 1)
    paginator_read = Paginator(read_notifications_list, 5)  # 5 اعلان در هر صفحه
    try:
        read_notifications = paginator_read.get_page(page_read)
    except PageNotAnInteger:
        read_notifications = paginator_read.get_page(1)
    except EmptyPage:
        read_notifications = paginator_read.get_page(paginator_read.num_pages)

    return render(request, 'dashboard/notification.html', {
        'unread_notifications': unread_notifications,
        'read_notifications': read_notifications,
    })


from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Notification


@login_required
def mark_notification_and_redirect(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        
        # اگر URL نوتیفیکیشن خالی باشد، به لیست جلسات هدایت می‌کنیم
        return redirect(notification.url if notification.url else 'meetings:meeting_list')
    except Notification.DoesNotExist:
        messages.error(request, 'نوتیفیکیشن مورد نظر یافت نشد.')
        return redirect('meetings:meeting_list')



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


@login_required
def activity_list(request):
    """نمایش لیست کامل فعالیت‌های کاربر"""
    
    # دریافت فعالیت‌های کاربر
    activities_list = request.user.activities.all()
    
    # فیلتر بر اساس نوع فعالیت (اگر در پارامترهای URL وجود داشته باشد)
    activity_type = request.GET.get('type')
    if activity_type:
        activities_list = activities_list.filter(activity_type=activity_type)
    
    # صفحه‌بندی
    paginator = Paginator(activities_list, 20)  # 20 فعالیت در هر صفحه
    page = request.GET.get('page')
    try:
        activities = paginator.page(page)
    except PageNotAnInteger:
        activities = paginator.page(1)
    except EmptyPage:
        activities = paginator.page(paginator.num_pages)
    
    return render(request, 'dashboard/activity_list.html', {
        'activities': activities,
        'activity_type': activity_type,
        'title': 'فعالیت‌های من',
    })


@login_required
def mark_all_notifications_as_read(request):
    """علامت‌گذاری همه اعلان‌های خوانده نشده کاربر به عنوان خوانده شده"""
    from .models import Notification
    
    # علامت‌گذاری همه اعلان‌های خوانده نشده
    count = Notification.mark_all_as_read(request.user)
    
    # اگر درخواست AJAX باشد، پاسخ JSON برگردان
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': f'{count} اعلان به عنوان خوانده شده علامت‌گذاری شد.',
            'count': count
        })
    
    # در غیر این صورت، به صفحه اعلان‌ها برگرد
    messages.success(request, f'{count} اعلان به عنوان خوانده شده علامت‌گذاری شد.')
    return redirect('dashboard:notification_list')


@login_required
def notification_detail(request, pk):
    """نمایش جزئیات یک اعلان"""
    from .models import Notification
    
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    
    # علامت‌گذاری اعلان به عنوان خوانده شده
    if not notification.is_read:
        notification.mark_as_read()
    
    context = {
        'notification': notification,
        'title': 'جزئیات اعلان',
    }
    
    return render(request, 'dashboard/notification_detail.html', context)
