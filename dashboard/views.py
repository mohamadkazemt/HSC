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
from permissions.utils import get_all_views_with_labels, check_permission
from permissions.models import UserPermission, PartPermission, SectionPermission, PositionPermission, UnitGroupPermission
from accounts.models import UnitGroup, UserProfile, DriverLicense
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseForbidden
from django.db.models import Count, Q
from datetime import timedelta
from .models_sms import SMSLog, SMSTemplate

name = 'dashboard'


@login_required
def dashboard(request):
    # بررسی اینکه آیا کاربر پرسنل اورژانس است (پرستار یا پزشک - نه مدیر)
    is_emergency_nurse = request.user.groups.filter(name='EmergencyNurse').exists()
    is_emergency_doctor = request.user.groups.filter(name='EmergencyDoctor').exists()
    is_emergency_manager = request.user.groups.filter(name='EmergencyManager').exists()
    
    # اگر کاربر پرستار یا پزشک است (نه مدیر) و سوپریوزر هم نیست، redirect به emergency
    if (is_emergency_nurse or is_emergency_doctor) and not is_emergency_manager and not request.user.is_superuser:
        messages.warning(request, 'شما فقط به بخش اورژانس دسترسی دارید.')
        from django.shortcuts import redirect
        return redirect('emergency_services:dashboard')
    
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
    
    # آمار موارد ثبت شده
    from anomalis.models import Anomaly
    from leave_reports.models import ShiftReport
    from checklist_app.models import Checklist
    from hse_incidents.models import IncidentReport
    from fire_reports.models import FireReport
    from risk_assessment.models import RiskAssessment
    from meetings.models import Meeting
    
    stats = {}
    
    # آمار ناهنجاری‌ها
    try:
        if request.user.is_superuser:
            stats['total_anomalies'] = Anomaly.objects.count()
            stats['completed_anomalies'] = Anomaly.objects.filter(status='completed').count()
            stats['in_progress_anomalies'] = Anomaly.objects.filter(status='in_progress').count()
        else:
            user_anomalies = Anomaly.objects.filter(created_by__user=request.user)
            stats['total_anomalies'] = user_anomalies.count()
            stats['completed_anomalies'] = user_anomalies.filter(status='completed').count()
            stats['in_progress_anomalies'] = user_anomalies.filter(status='in_progress').count()
    except Exception as e:
        print(f"Error in anomalies stats: {e}")
        pass
    
    # آمار مرخصی‌ها
    try:
        user_leaves = ShiftReport.objects.filter(user=request.user)
        stats['total_leaves'] = user_leaves.count()
        stats['approved_leaves'] = user_leaves.filter(status='approved').count()
        stats['pending_leaves'] = user_leaves.filter(status__in=['pending_replacement', 'pending_approval']).count()
    except Exception as e:
        print(f"Error in leaves stats: {e}")
        pass
    
    # آمار چک لیست‌ها
    try:
        if request.user.is_superuser:
            stats['total_checklists'] = Checklist.objects.count()
        else:
            stats['total_checklists'] = Checklist.objects.filter(user=request.user).count()
    except Exception as e:
        print(f"Error in checklists stats: {e}")
        pass
    
    # آمار حوادث HSE
    try:
        if request.user.is_superuser:
            stats['total_incidents'] = IncidentReport.objects.count()
        else:
            # IncidentReport فیلد report_author دارد که UserProfile است
            user_profile = getattr(request.user, 'userprofile', None)
            if user_profile:
                stats['total_incidents'] = IncidentReport.objects.filter(report_author=user_profile).count()
            else:
                stats['total_incidents'] = 0
    except Exception as e:
        print(f"Error in incidents stats: {e}")
        pass
    
    # آمار گزارشات آتش
    try:
        if request.user.is_superuser:
            stats['total_fire_reports'] = FireReport.objects.count()
        else:
            # FireReport فیلد shift_operator و firefighter دارد
            stats['total_fire_reports'] = FireReport.objects.filter(
                Q(shift_operator=request.user) | Q(firefighter=request.user)
            ).count()
    except Exception as e:
        print(f"Error in fire reports stats: {e}")
        pass
    
    # آمار ارزیابی ریسک
    try:
        if request.user.is_superuser:
            stats['total_risks'] = RiskAssessment.objects.count()
        else:
            # RiskAssessment فیلد created_by دارد که UserProfile است
            user_profile = getattr(request.user, 'userprofile', None)
            if user_profile:
                stats['total_risks'] = RiskAssessment.objects.filter(created_by=user_profile).count()
            else:
                stats['total_risks'] = 0
    except Exception as e:
        print(f"Error in risks stats: {e}")
        pass
    
    # آمار جلسات
    try:
        from datetime import date, time
        today = date.today()
        now_time = timezone.now().time()
        
        if request.user.is_superuser:
            stats['total_meetings'] = Meeting.objects.count()
            # جلسات آینده: تاریخ بعد از امروز یا تاریخ امروز با ساعت بعد از الان
            stats['upcoming_meetings'] = Meeting.objects.filter(
                Q(date__gt=today) | Q(date=today, start_time__gte=now_time),
                status='scheduled'
            ).count()
        else:
            user_meetings = Meeting.objects.filter(participants=request.user)
            stats['total_meetings'] = user_meetings.count()
            stats['upcoming_meetings'] = user_meetings.filter(
                Q(date__gt=today) | Q(date=today, start_time__gte=now_time),
                status='scheduled'
            ).count()
    except Exception as e:
        print(f"Error in meetings stats: {e}")
        pass

    # برای اطمینان از وجود داده‌ها، یک لاگ اضافه کنید
    print(f"Recent activities count: {recent_activities.count()}")
    
    # ============= دسته‌بندی آمارها بر اساس واحدها =============
    stats_by_category = {}
    
    # واحد اداری
    if stats.get('total_leaves') is not None or stats.get('pending_leaves') is not None:
        # بررسی دسترسی به مرخصی‌ها
        if request.user.is_superuser or check_permission(request.user, 'request_leave').get('can_view', False):
            stats_by_category['واحد اداری'] = {
                'icon': 'M18 18.72a9.094 9.094 0 0 0 3.741-.479 3 3 0 0 0-4.682-2.72m.94 3.198.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0 1 12 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 0 1 6 18.719m12 0a5.971 5.971 0 0 0-.941-3.197m0 0A5.995 5.995 0 0 0 12 12.75a5.995 5.995 0 0 0-5.058 2.772m0 0a3 3 0 0 0-4.681 2.72 8.986 8.986 0 0 0 3.74.477m.94-3.197a5.971 5.971 0 0 0-.94 3.197M15 6.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm6 3a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Zm-13.5 0a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Z',
                'color': 'indigo',
                'stats': [
                    {'label': 'مرخصی‌ها', 'value': stats.get('total_leaves', 0), 'url': 'leave_reports:my_inbox', 'icon': 'M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5', 'gradient': 'from-purple-500 via-purple-600 to-indigo-600', 'sub_value': stats.get('pending_leaves', 0), 'sub_label': 'در انتظار'},
                ]
            }
    
    # واحد ایمنی (HSEC)
    hsec_stats = []
    if stats.get('total_incidents') is not None:
        if request.user.is_superuser or check_permission(request.user, 'incident_report').get('can_view', False):
            hsec_stats.append({'label': 'حوادث HSE', 'value': stats.get('total_incidents', 0), 'url': 'hse_incidents:list_reports', 'icon': 'M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z', 'gradient': 'from-orange-500 via-orange-600 to-amber-600'})
    if stats.get('total_fire_reports') is not None:
        if request.user.is_superuser or check_permission(request.user, 'report_create').get('can_view', False):
            hsec_stats.append({'label': 'گزارشات آتش', 'value': stats.get('total_fire_reports', 0), 'url': 'fire_reports:report_list', 'icon': 'M15.362 5.214A8.252 8.252 0 0 1 12 21 8.25 8.25 0 0 1 6.038 7.047 8.287 8.287 0 0 0 9 9.601a8.983 8.983 0 0 1 3.361-6.867 8.21 8.21 0 0 1 3 2.48Z', 'gradient': 'from-rose-500 via-rose-600 to-pink-600'})
    if hsec_stats:
        stats_by_category['واحد ایمنی (HSEC)'] = {
            'icon': 'M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z',
            'color': 'green',
            'stats': hsec_stats
        }
    
    # چک لیست‌ها
    if stats.get('total_checklists') is not None:
        if request.user.is_superuser or check_permission(request.user, 'general_checklist_form').get('can_view', False):
            stats_by_category['چک لیست‌ها'] = {
                'icon': 'M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z',
                'color': 'blue',
                'stats': [
                    {'label': 'چک لیست‌ها', 'value': stats.get('total_checklists', 0), 'url': 'checklist_app:general_checklist_list', 'icon': 'M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z', 'gradient': 'from-blue-500 via-blue-600 to-cyan-600'},
                ]
            }
    
    # ناهنجاری‌ها
    if stats.get('total_anomalies') is not None:
        if request.user.is_superuser or check_permission(request.user, 'anomalis').get('can_view', False):
            anomaly_stat = {'label': 'ناهنجاری‌ها', 'value': stats.get('total_anomalies', 0), 'url': 'anomalis:list', 'icon': 'M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z', 'gradient': 'from-red-500 via-red-600 to-red-700', 'sub_value': stats.get('completed_anomalies', 0), 'sub_label': 'تکمیل شده'}
            stats_by_category['ناهنجاری‌ها'] = {
                'icon': 'M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z',
                'color': 'red',
                'stats': [anomaly_stat]
            }
    
    # ارزیابی ریسک
    if stats.get('total_risks') is not None:
        if request.user.is_superuser or check_permission(request.user, 'risk_create').get('can_view', False):
            stats_by_category['ارزیابی ریسک'] = {
                'icon': 'M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z',
                'color': 'amber',
                'stats': [
                    {'label': 'ارزیابی ریسک', 'value': stats.get('total_risks', 0), 'url': 'risk_assessment:risk_list', 'icon': 'M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z', 'gradient': 'from-amber-500 via-amber-600 to-yellow-600'},
                ]
            }
    
    # مدیریت جلسات
    if stats.get('total_meetings') is not None:
        if request.user.is_superuser or check_permission(request.user, 'meeting_create').get('can_view', False):
            stats_by_category['مدیریت جلسات'] = {
                'icon': 'M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5',
                'color': 'teal',
                'stats': [
                    {'label': 'جلسات', 'value': stats.get('total_meetings', 0), 'url': 'meetings:meeting_list', 'icon': 'M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5', 'gradient': 'from-teal-500 via-teal-600 to-cyan-600', 'sub_value': stats.get('upcoming_meetings', 0), 'sub_label': 'پیش‌رو'},
                ]
            }
    
    # ============= فرم‌های پراستفاده و دسترسی سریع (دسته‌بندی شده) =============
    
    # تعریف فرم‌های پراستفاده با دسته‌بندی بر اساس سایدبار
    quick_access_forms_by_category = {
        'واحد اداری': {
            'icon': 'M18 18.72a9.094 9.094 0 0 0 3.741-.479 3 3 0 0 0-4.682-2.72m.94 3.198.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0 1 12 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 0 1 6 18.719m12 0a5.971 5.971 0 0 0-.941-3.197m0 0A5.995 5.995 0 0 0 12 12.75a5.995 5.995 0 0 0-5.058 2.772m0 0a3 3 0 0 0-4.681 2.72 8.986 8.986 0 0 0 3.74.477m.94-3.197a5.971 5.971 0 0 0-.94 3.197M15 6.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm6 3a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Zm-13.5 0a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Z',
            'color': 'indigo',
            'forms': [
                {
                    'name': 'request_leave',
                    'app': 'leave_reports',
                    'url': 'leave_reports:request_leave',
                    'label': 'درخواست مرخصی',
                    'icon': 'M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5',
                    'color': 'purple',
                    'bg_gradient': 'from-purple-500 to-purple-600',
                    'hover': 'hover:from-purple-600 hover:to-purple-700',
                },
            ]
        },
        'واحد ایمنی (HSEC)': {
            'icon': 'M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z',
            'color': 'green',
            'forms': [
                {
                    'name': 'daily_report_form',
                    'app': 'dailyreport_hse',
                    'url': 'dailyreport_hse:daily_report_form',
                    'label': 'گزارش روزانه HSE',
                    'icon': 'M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z',
                    'color': 'green',
                    'bg_gradient': 'from-green-500 to-green-600',
                    'hover': 'hover:from-green-600 hover:to-green-700',
                },
                {
                    'name': 'incident_report',
                    'app': 'hse_incidents',
                    'url': 'hse_incidents:incident_report',
                    'label': 'گزارش حادثه HSE',
                    'icon': 'M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z',
                    'color': 'orange',
                    'bg_gradient': 'from-orange-500 to-orange-600',
                    'hover': 'hover:from-orange-600 hover:to-orange-700',
                },
                {
                    'name': 'report_create',
                    'app': 'fire_reports',
                    'url': 'fire_reports:report_create',
                    'label': 'گزارش آتش',
                    'icon': 'M15.362 5.214A8.252 8.252 0 0 1 12 21 8.25 8.25 0 0 1 6.038 7.047 8.287 8.287 0 0 0 9 9.601a8.983 8.983 0 0 1 3.361-6.867 8.21 8.21 0 0 1 3 2.48Z',
                    'color': 'rose',
                    'bg_gradient': 'from-rose-500 to-rose-600',
                    'hover': 'hover:from-rose-600 hover:to-rose-700',
                },
                {
                    'name': 'extinguisher_list',
                    'app': 'fire_extinguisher_management',
                    'url': 'fire_extinguisher_management:extinguisher_list',
                    'label': 'کپسول آتش‌نشانی',
                    'icon': 'M15.362 5.214A8.252 8.252 0 0 1 12 21 8.25 8.25 0 0 1 6.038 7.047 8.287 8.287 0 0 0 9 9.601a8.983 8.983 0 0 1 3.361-6.867 8.21 8.21 0 0 1 3 2.48Z',
                    'color': 'pink',
                    'bg_gradient': 'from-pink-500 to-pink-600',
                    'hover': 'hover:from-pink-600 hover:to-pink-700',
                },
            ]
        },
        'چک لیست‌ها': {
            'icon': 'M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z',
            'color': 'blue',
            'forms': [
                {
                    'name': 'general_checklist_form',
                    'app': 'checklist_app',
                    'url': 'checklist_app:general_checklist_form',
                    'label': 'چک لیست جدید',
                    'icon': 'M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z',
                    'color': 'blue',
                    'bg_gradient': 'from-blue-500 to-blue-600',
                    'hover': 'hover:from-blue-600 hover:to-blue-700',
                },
                {
                    'name': 'checklist_form',
                    'app': 'machine_checklist',
                    'url': 'machine_checklist:checklist_form',
                    'label': 'چک لیست ماشین‌آلات',
                    'icon': 'M10.5 1.5H8.25A2.25 2.25 0 0 0 6 3.75v16.5a2.25 2.25 0 0 0 2.25 2.25h7.5A2.25 2.25 0 0 0 18 20.25V3.75a2.25 2.25 0 0 0-2.25-2.25H13.5m-3 0V3h3V1.5m-3 0h3m-3 18.75h3',
                    'color': 'indigo',
                    'bg_gradient': 'from-indigo-500 to-indigo-600',
                    'hover': 'hover:from-indigo-600 hover:to-indigo-700',
                },
            ]
        },
        'ناهنجاری‌ها': {
            'icon': 'M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z',
            'color': 'red',
            'forms': [
                {
                    'name': 'anomalis',
                    'app': 'anomalis',
                    'url': 'anomalis:anomalis',
                    'label': 'ثبت ناهنجاری',
                    'icon': 'M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z',
                    'color': 'red',
                    'bg_gradient': 'from-red-500 to-red-600',
                    'hover': 'hover:from-red-600 hover:to-red-700',
                },
            ]
        },
        'ارزیابی ریسک': {
            'icon': 'M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z',
            'color': 'amber',
            'forms': [
                {
                    'name': 'risk_create',
                    'app': 'risk_assessment',
                    'url': 'risk_assessment:risk_create',
                    'label': 'ارزیابی ریسک',
                    'icon': 'M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z',
                    'color': 'amber',
                    'bg_gradient': 'from-amber-500 to-amber-600',
                    'hover': 'hover:from-amber-600 hover:to-amber-700',
                },
            ]
        },
        'مدیریت جلسات': {
            'icon': 'M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5',
            'color': 'teal',
            'forms': [
                {
                    'name': 'meeting_create',
                    'app': 'meetings',
                    'url': 'meetings:meeting_create',
                    'label': 'ایجاد جلسه',
                    'icon': 'M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5',
                    'color': 'teal',
                    'bg_gradient': 'from-teal-500 to-teal-600',
                    'hover': 'hover:from-teal-600 hover:to-teal-700',
                },
            ]
        },
    }
    
    # فیلتر کردن فرم‌ها بر اساس دسترسی کاربر و دسته‌بندی
    accessible_forms_by_category = {}
    for category_name, category_data in quick_access_forms_by_category.items():
        accessible_forms = []
        for form in category_data['forms']:
            # بررسی دسترسی - اگر سوپریوزر است یا دسترسی دارد
            if request.user.is_superuser:
                accessible_forms.append(form)
            else:
                # بررسی دسترسی با استفاده از سیستم permissions
                permissions = check_permission(request.user, form['name'])
                if permissions.get('can_view', False) or permissions.get('can_add', False):
                    accessible_forms.append(form)
        
        # فقط دسته‌هایی که حداقل یک فرم قابل دسترسی دارند را اضافه می‌کنیم
        if accessible_forms:
            accessible_forms_by_category[category_name] = {
                'icon': category_data['icon'],
                'color': category_data['color'],
                'forms': accessible_forms
            }
    
    context = {
        'unread_notifications_count': unread_notifications_count,
        'recent_notifications': recent_notifications,
        'recent_activities': recent_activities,  # اضافه کردن فعالیت‌های اخیر
        'user_access_permissions': user_access_permissions,
        'stats': stats,
        'stats_by_category': stats_by_category,
        'title': 'داشبورد',
        'license_warning': license_warning,
        'driver_license': driver_license,
        # کارتابل مرخصی‌ها
        'pending_replacement_approvals': pending_replacement_approvals,
        'pending_manager_approvals': pending_manager_approvals,
        # فرم‌های دسترسی سریع (دسته‌بندی شده)
        'quick_access_forms_by_category': accessible_forms_by_category,
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


@staff_member_required
def admin_overview(request):
    """نمای کلی مدیریتی برای سوپر یوزرها: آمار پیامک‌ها و اعلان‌ها."""
    if not request.user.is_superuser:
        return HttpResponseForbidden("Only superusers may access this page.")

    now = timezone.now()
    start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    last24 = now - timedelta(hours=24)

    # Metrics
    sms_today = SMSLog.objects.filter(created_at__gte=start_today).count()
    sms_failed_24h = SMSLog.objects.filter(created_at__gte=last24, status__in=["failed", "rate_limited"]).count()
    notif_unread = Notification.objects.filter(is_read=False).count()
    active_templates = SMSTemplate.objects.filter(is_active=True).count()

    # Top templates by usage
    top_templates = SMSTemplate.objects.order_by('-usage_count')[:5]

    # Recent SMS logs
    recent_sms = SMSLog.objects.order_by('-created_at')[:10]

    context = {
        'title': 'نمای کلی مدیریت',
        'sms_today': sms_today,
        'sms_failed_24h': sms_failed_24h,
        'notif_unread': notif_unread,
        'active_templates': active_templates,
        'top_templates': top_templates,
        'recent_sms': recent_sms,
    }
    return render(request, 'dashboard/admin_overview.html', context)
