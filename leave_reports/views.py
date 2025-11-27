"""
Views برای سیستم مدیریت درخواست‌های مرخصی و تأیید
"""
import json
import datetime
import jdatetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User
from django.db import transaction

from .models import ShiftReport, ApprovalHierarchy
from .forms import LeaveRequestForm, RejectLeaveForm, ApprovalHierarchyForm, LeaveSearchForm
from accounts.models import UserProfile
from dashboard.utils import log_user_activity
from permissions.utils import check_permission


# ============= درخواست مرخصی جدید =============

@login_required
def request_leave(request):
    """صفحه درخواست مرخصی جدید"""
    
    # بررسی دسترسی
    if not check_permission(request.user, 'request_leave'):
        messages.error(request, 'شما دسترسی به این بخش را ندارید.')
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    leave_request = form.save(commit=False)
                    leave_request.user = request.user
                    
                    # برای غیبت، استعلاجی و ساعتی نیازی به تأیید جایگزین نیست
                    if leave_request.leave_type in ['absence', 'sick_leave', 'hourly']:
                        leave_request.status = 'pending_approval'
                        leave_request.replacement_approved = True
                        leave_request.replacement_approved_at = timezone.now()
                    else:
                        leave_request.status = 'pending_replacement'
                    
                    # تنظیم گروه کاری و سایر فیلدها
                    if hasattr(request.user, 'userprofile'):
                        leave_request.work_group = request.user.userprofile.group or 'نامشخص'
                        leave_request.crate_by = request.user.userprofile
                    
                    leave_request.save()
                    
                    # ثبت فعالیت
                    log_user_activity(
                        user=request.user,
                        activity_type='create',
                        description=f'ثبت درخواست مرخصی {leave_request.get_leave_type_display()} برای تاریخ {leave_request.shift_date}',
                        related_model='ShiftReport',
                        related_object_id=leave_request.id,
                        url=reverse('leave_reports:my_inbox'),
                        request=request
                    )
                    
                    # ارسال اعلان به جایگزین یا مدیر
                    if leave_request.status == 'pending_replacement':
                        # اگر نیاز به تأیید جایگزین داشت، به جایگزین اطلاع می‌دهیم
                        from .utils import send_notification_to_replacement
                        send_notification_to_replacement(leave_request)
                    elif leave_request.status == 'pending_approval':
                        # اگر مستقیم رفت به مدیر (مثل غیبت، استعلاجی)، به مدیر اطلاع می‌دهیم
                        from .utils import send_notification_to_manager
                        send_notification_to_manager(leave_request)
                    
                    messages.success(request, 'درخواست مرخصی شما با موفقیت ثبت شد و برای جایگزین ارسال شد.')
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'status': 'success',
                            'message': 'درخواست با موفقیت ثبت شد',
                            'redirect_url': reverse('leave_reports:my_inbox')
                        })
                    
                    return redirect('leave_reports:my_inbox')
                    
            except Exception as e:
                messages.error(request, f'خطا در ثبت درخواست: {str(e)}')
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'error',
                        'message': str(e)
                    }, status=400)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'خطا در اعتبارسنجی فرم',
                    'errors': form.errors
                }, status=400)
    else:
        form = LeaveRequestForm(user=request.user)
        
        # ثبت فعالیت مشاهده فرم
        log_user_activity(
            user=request.user,
            activity_type='view',
            description='مشاهده فرم درخواست مرخصی',
            related_model='ShiftReport',
            related_object_id=None,
            url=reverse('leave_reports:request_leave'),
            request=request
        )
    
    # Get today's date in Persian (Jalali) format for date picker minDate
    today_jalali = jdatetime.date.today().strftime('%Y/%m/%d')
    
    return render(request, 'leave_reports/request_leave.html', {
        'form': form,
        'page_title': 'درخواست مرخصی جدید',
        'today_jalali': today_jalali,
    })


# ============= کارتابل من =============

@login_required
def my_inbox(request):
    """صفحه کارتابل من - نمایش درخواست‌های خودم و درخواست‌های منتظر تأیید من"""
    
    # بررسی دسترسی
    if not check_permission(request.user, 'my_inbox'):
        messages.error(request, 'شما دسترسی به این بخش را ندارید.')
        return redirect('dashboard:dashboard')
    
    # تب فعال
    active_tab = request.GET.get('tab', 'my_requests')
    
    # درخواست‌های من
    my_requests = ShiftReport.objects.filter(user=request.user).select_related(
        'replacement_person', 'final_approver', 'rejected_by', 'crate_by'
    ).order_by('-created_at')
    
    # درخواست‌های منتظر تأیید من
    pending_for_me = ShiftReport.objects.none()
    
    # 1. درخواست‌هایی که من جایگزین آن‌ها هستم
    pending_as_replacement = ShiftReport.objects.filter(
        replacement_person=request.user,
        status='pending_replacement',
        replacement_approved=False
    ).select_related('user', 'crate_by')
    
    # 2. درخواست‌هایی که باید به عنوان مدیر تأیید کنم
    # استفاده از منطق جدید: بررسی همه درخواست‌های pending_approval
    # و بررسی اینکه آیا کاربر فعلی تأیید کننده آن‌ها است یا نه
    pending_as_manager = ShiftReport.objects.none()
    if hasattr(request.user, 'userprofile'):
        user_profile = request.user.userprofile
        
        # پیدا کردن همه درخواست‌های pending_approval
        all_pending = ShiftReport.objects.filter(
            status='pending_approval',
            replacement_approved=True
        ).select_related('user', 'replacement_person', 'crate_by', 'user__userprofile')
        
        # فیلتر کردن درخواست‌هایی که کاربر فعلی می‌تواند آن‌ها را تأیید کند
        matching_leaves = []
        for leave in all_pending:
            approver = leave.get_required_approver()
            if approver and approver == user_profile:
                matching_leaves.append(leave.id)
        
        # تبدیل به QuerySet
        if matching_leaves:
            pending_as_manager = ShiftReport.objects.filter(
                id__in=matching_leaves
            ).select_related('user', 'replacement_person', 'crate_by')
    
    # ترکیب درخواست‌های منتظر
    pending_for_me = (pending_as_replacement | pending_as_manager).distinct().order_by('-created_at')
    
    # محاسبه آمارها
    my_requests_count = my_requests.count()
    pending_replacement_count = pending_as_replacement.count()
    pending_manager_count = pending_as_manager.count()
    approved_count = my_requests.filter(status='approved').count()
    
    # Pagination برای درخواست‌های من
    my_page = request.GET.get('my_page', 1)
    my_paginator = Paginator(my_requests, 10)
    try:
        my_requests_page = my_paginator.page(my_page)
    except PageNotAnInteger:
        my_requests_page = my_paginator.page(1)
    except EmptyPage:
        my_requests_page = my_paginator.page(my_paginator.num_pages)
    
    # Pagination برای درخواست‌های منتظر
    pending_page = request.GET.get('pending_page', 1)
    pending_paginator = Paginator(pending_for_me, 10)
    try:
        pending_page_obj = pending_paginator.page(pending_page)
    except PageNotAnInteger:
        pending_page_obj = pending_paginator.page(1)
    except EmptyPage:
        pending_page_obj = pending_paginator.page(pending_paginator.num_pages)
    
    # ثبت فعالیت
    log_user_activity(
        user=request.user,
        activity_type='view',
        description='مشاهده کارتابل مرخصی',
        related_model='ShiftReport',
        related_object_id=None,
        url=reverse('leave_reports:my_inbox'),
        request=request
    )
    
    return render(request, 'leave_reports/my_inbox.html', {
        'my_requests': my_requests_page,
        'pending_approvals': pending_page_obj,
        'my_requests_count': my_requests_count,
        'pending_replacement_count': pending_replacement_count,
        'pending_manager_count': pending_manager_count,
        'approved_count': approved_count,
        'active_tab': active_tab,
        'page_title': 'کارتابل مرخصی',
    })


# ============= تأیید/رد توسط جایگزین =============

@login_required
def approve_as_replacement(request, leave_id):
    """تأیید درخواست توسط جایگزین"""
    
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"🔵 approve_as_replacement called - leave_id: {leave_id}, user: {request.user}")
    
    leave_request = get_object_or_404(ShiftReport, id=leave_id)
    logger.info(f"  Leave request found: {leave_request}, status: {leave_request.status}")
    logger.info(f"  Replacement person: {leave_request.replacement_person}, current user: {request.user}")
    
    # بررسی دسترسی
    if leave_request.replacement_person != request.user:
        logger.warning(f"❌ Access denied - replacement_person mismatch")
        return JsonResponse({
            'status': 'error',
            'message': 'شما مجاز به انجام این عملیات نیستید'
        }, status=403)
    
    if leave_request.status != 'pending_replacement':
        logger.warning(f"❌ Invalid status - current: {leave_request.status}, expected: pending_replacement")
        return JsonResponse({
            'status': 'error',
            'message': 'این درخواست قابل تأیید نیست'
        }, status=400)
    
    try:
        logger.info(f"✅ Proceeding with approval...")
        with transaction.atomic():
            leave_request.replacement_approved = True
            leave_request.replacement_approved_at = timezone.now()
            leave_request.status = 'pending_approval'
            leave_request.save()
            logger.info(f"✅ Leave request updated successfully")
            
            # ثبت فعالیت
            log_user_activity(
                user=request.user,
                activity_type='update',
                description=f'تأیید جایگزینی برای درخواست مرخصی {leave_request.user.get_full_name()}',
                related_model='ShiftReport',
                related_object_id=leave_request.id,
                url=None,
                request=request
            )
            
            # ارسال اعلان به مدیر و درخواست دهنده
            from .utils import send_notification_to_manager, send_notification_to_requester_approved
            send_notification_to_manager(leave_request)
            send_notification_to_requester_approved(leave_request, approved_by_type='replacement')
            
            logger.info(f"✅ Approval completed successfully")
            return JsonResponse({
                'status': 'success',
                'message': 'تأیید جایگزینی با موفقیت انجام شد. درخواست برای تأیید نهایی ارسال شد.'
            })
            
    except Exception as e:
        logger.error(f"❌ Error in approval: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'خطا در تأیید: {str(e)}'
        }, status=500)


@login_required
def reject_as_replacement(request, leave_id):
    """رد درخواست توسط جایگزین"""
    
    leave_request = get_object_or_404(ShiftReport, id=leave_id)
    
    # بررسی دسترسی
    if leave_request.replacement_person != request.user:
        return JsonResponse({
            'status': 'error',
            'message': 'شما مجاز به انجام این عملیات نیستید'
        }, status=403)
    
    if leave_request.status != 'pending_replacement':
        return JsonResponse({
            'status': 'error',
            'message': 'این درخواست قابل رد نیست'
        }, status=400)
    
    if request.method == 'POST':
        form = RejectLeaveForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    leave_request.status = 'rejected'
                    leave_request.rejection_reason = form.cleaned_data['rejection_reason']
                    leave_request.rejected_by = request.user
                    leave_request.rejected_at = timezone.now()
                    leave_request.save()
                    
                    # ثبت فعالیت
                    log_user_activity(
                        user=request.user,
                        activity_type='update',
                        description=f'رد جایگزینی برای درخواست مرخصی {leave_request.user.get_full_name()}',
                        related_model='ShiftReport',
                        related_object_id=leave_request.id,
                        url=None,
                        request=request
                    )
                    
                    # ارسال اعلان به درخواست دهنده
                    from .utils import send_notification_to_requester_rejected
                    send_notification_to_requester_rejected(leave_request, rejected_by_type='replacement')
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'درخواست با موفقیت رد شد'
                    })
                    
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'خطا در رد درخواست: {str(e)}'
                }, status=500)
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'خطا در اعتبارسنجی فرم',
                'errors': form.errors
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'متد درخواست نامعتبر است'
    }, status=405)


# ============= تأیید/رد توسط مدیر =============

@login_required
def approve_as_manager(request, leave_id):
    """تأیید نهایی درخواست توسط مدیر"""
    
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"🟢 approve_as_manager called - leave_id: {leave_id}, user: {request.user}")
    
    leave_request = get_object_or_404(ShiftReport, id=leave_id)
    logger.info(f"  Leave request found: {leave_request}, status: {leave_request.status}")
    
    can_approve = leave_request.can_be_approved_by(request.user)
    logger.info(f"  can_be_approved_by result: {can_approve}")
    
    # بررسی دسترسی
    if not can_approve:
        logger.warning(f"❌ Access denied - user cannot approve this request")
        return JsonResponse({
            'status': 'error',
            'message': 'شما مجاز به انجام این عملیات نیستید'
        }, status=403)
    
    if leave_request.status != 'pending_approval':
        logger.warning(f"❌ Invalid status - current: {leave_request.status}, expected: pending_approval")
        return JsonResponse({
            'status': 'error',
            'message': 'این درخواست قابل تأیید نیست'
        }, status=400)
    
    try:
        logger.info(f"✅ Proceeding with manager approval...")
        with transaction.atomic():
            leave_request.status = 'approved'
            leave_request.final_approver = request.user.userprofile
            leave_request.final_approved_at = timezone.now()
            leave_request.registration = True
            leave_request.save()
            logger.info(f"✅ Leave request approved successfully")
            
            # ثبت فعالیت
            log_user_activity(
                user=request.user,
                activity_type='update',
                description=f'تأیید نهایی درخواست مرخصی {leave_request.user.get_full_name()}',
                related_model='ShiftReport',
                related_object_id=leave_request.id,
                url=None,
                request=request
            )
            
            # ارسال اعلان به درخواست دهنده
            from .utils import send_notification_to_requester_approved
            send_notification_to_requester_approved(leave_request, approved_by_type='manager')
            
            logger.info(f"✅ Manager approval completed successfully")
            return JsonResponse({
                'status': 'success',
                'message': 'درخواست با موفقیت تأیید شد'
            })
            
    except Exception as e:
        logger.error(f"❌ Error in manager approval: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'خطا در تأیید: {str(e)}'
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'خطا در تأیید: {str(e)}'
        }, status=500)


@login_required
def reject_as_manager(request, leave_id):
    """رد نهایی درخواست توسط مدیر"""
    
    leave_request = get_object_or_404(ShiftReport, id=leave_id)
    
    # بررسی دسترسی
    if not leave_request.can_be_approved_by(request.user):
        return JsonResponse({
            'status': 'error',
            'message': 'شما مجاز به انجام این عملیات نیستید'
        }, status=403)
    
    if leave_request.status != 'pending_approval':
        return JsonResponse({
            'status': 'error',
            'message': 'این درخواست قابل رد نیست'
        }, status=400)
    
    if request.method == 'POST':
        form = RejectLeaveForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    leave_request.status = 'rejected'
                    leave_request.rejection_reason = form.cleaned_data['rejection_reason']
                    leave_request.rejected_by = request.user
                    leave_request.rejected_at = timezone.now()
                    leave_request.save()
                    
                    # ثبت فعالیت
                    log_user_activity(
                        user=request.user,
                        activity_type='update',
                        description=f'رد نهایی درخواست مرخصی {leave_request.user.get_full_name()}',
                        related_model='ShiftReport',
                        related_object_id=leave_request.id,
                        url=None,
                        request=request
                    )
                    
                    # ارسال اعلان به درخواست دهنده
                    from .utils import send_notification_to_requester_rejected
                    send_notification_to_requester_rejected(leave_request, rejected_by_type='manager')
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'درخواست با موفقیت رد شد'
                    })
                    
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'خطا در رد درخواست: {str(e)}'
                }, status=500)
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'خطا در اعتبارسنجی فرم',
                'errors': form.errors
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'متد درخواست نامعتبر است'
    }, status=405)


# ============= آرشیو مرخصی‌ها =============

@login_required
def leave_archive(request):
    """صفحه آرشیو و جستجوی مرخصی‌ها"""
    
    # بررسی دسترسی
    if not check_permission(request.user, 'leave_archive'):
        messages.error(request, 'شما دسترسی به این بخش را ندارید.')
        return redirect('dashboard:dashboard')
    
    form = LeaveSearchForm(request.GET)
    leaves = ShiftReport.objects.all().select_related(
        'user', 'replacement_person', 'final_approver', 'rejected_by', 'crate_by'
    )
    
    # فیلتر بر اساس جستجو
    if form.is_valid():
        user_search = form.cleaned_data.get('user_search')
        if user_search:
            leaves = leaves.filter(
                Q(user__first_name__icontains=user_search) |
                Q(user__last_name__icontains=user_search) |
                Q(user__username__icontains=user_search)
            )
        
        status = form.cleaned_data.get('status')
        if status:
            leaves = leaves.filter(status=status)
        
        leave_type = form.cleaned_data.get('leave_type')
        if leave_type:
            leaves = leaves.filter(leave_type=leave_type)
        
        shift_type = form.cleaned_data.get('shift_type')
        if shift_type:
            leaves = leaves.filter(shift_type=shift_type)
        
        work_group = form.cleaned_data.get('work_group')
        if work_group:
            leaves = leaves.filter(work_group__icontains=work_group)
        
        date_from = form.cleaned_data.get('date_from')
        if date_from:
            try:
                # تبدیل تاریخ شمسی به میلادی
                if '/' in date_from:
                    year, month, day = map(int, date_from.split('/'))
                elif '-' in date_from:
                    year, month, day = map(int, date_from.split('-'))
                jalali_date = jdatetime.date(year, month, day)
                gregorian_date = jalali_date.togregorian()
                leaves = leaves.filter(shift_date__gte=gregorian_date)
            except:
                pass
        
        date_to = form.cleaned_data.get('date_to')
        if date_to:
            try:
                # تبدیل تاریخ شمسی به میلادی
                if '/' in date_to:
                    year, month, day = map(int, date_to.split('/'))
                elif '-' in date_to:
                    year, month, day = map(int, date_to.split('-'))
                jalali_date = jdatetime.date(year, month, day)
                gregorian_date = jalali_date.togregorian()
                leaves = leaves.filter(shift_date__lte=gregorian_date)
            except:
                pass
    
    leaves = leaves.order_by('-created_at')
    
    # اگر درخواست خروجی اکسل باشد
    if request.GET.get('export') == 'excel':
        return export_leaves_to_excel(leaves)
    
    # محاسبه آمار
    from django.utils import timezone
    total_count = leaves.count()
    pending_count = leaves.filter(
        Q(status='pending_replacement') | Q(status='pending_approval')
    ).count()
    approved_count = leaves.filter(status='approved').count()
    rejected_count = leaves.filter(status='rejected').count()
    today_count = leaves.filter(shift_date=timezone.now().date()).count()
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(leaves, 20)
    try:
        leaves_page = paginator.page(page)
    except PageNotAnInteger:
        leaves_page = paginator.page(1)
    except EmptyPage:
        leaves_page = paginator.page(paginator.num_pages)
    
    # ثبت فعالیت
    log_user_activity(
        user=request.user,
        activity_type='view',
        description='مشاهده آرشیو مرخصی‌ها',
        related_model='ShiftReport',
        related_object_id=None,
        url=reverse('leave_reports:leave_archive'),
        request=request
    )
    
    # Get today's date in Persian (Jalali) format for date picker (optional, for archive search)
    today_jalali = jdatetime.date.today().strftime('%Y/%m/%d')
    
    return render(request, 'leave_reports/leave_archive.html', {
        'form': form,
        'page_obj': leaves_page,
        'total_count': total_count,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'today_count': today_count,
        'page_title': 'آرشیو مرخصی‌ها',
        'today_jalali': today_jalali,
    })


def export_leaves_to_excel(leaves):
    """خروجی اکسل درخواست‌های مرخصی"""
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        return HttpResponse("لطفاً کتابخانه openpyxl را نصب کنید", status=500)
    
    # ایجاد workbook و worksheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "گزارش مرخصی‌ها"
    
    # تنظیمات RTL
    ws.sheet_view.rightToLeft = True
    
    # تعریف استایل‌ها
    header_font = Font(bold=True, size=12, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    cell_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # عناوین ستون‌ها
    headers = [
        'ردیف',
        'نام و نام خانوادگی',
        'کد پرسنلی',
        'گروه کاری',
        'نوع مرخصی',
        'تاریخ شیفت',
        'نوع شیفت',
        'وضعیت',
        'جانشین',
        'کد پرسنلی جانشین',
        'تأیید کننده نهایی',
        'کد پرسنلی تأیید کننده',
        'تاریخ ثبت',
        'توضیحات'
    ]
    
    # نوشتن هدر
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = border
    
    # نوشتن داده‌ها
    status_dict = {
        'pending_replacement': 'در انتظار جانشین',
        'pending_approval': 'در انتظار تأیید',
        'approved': 'تأیید شده',
        'rejected': 'رد شده'
    }
    
    leave_type_dict = {
        'regular': 'استحقاقی',
        'sick_leave': 'استعلاجی',
        'hourly': 'ساعتی',
        'other': 'سایر'
    }
    
    shift_type_dict = {
        'day': 'روز',
        'night': 'شب',
        'extra': 'اضافه کاری'
    }
    
    for idx, leave in enumerate(leaves, 2):
        # تبدیل تاریخ میلادی به شمسی
        shift_date_jalali = jdatetime.date.fromgregorian(date=leave.shift_date).strftime('%Y/%m/%d')
        created_at_jalali = jdatetime.datetime.fromgregorian(datetime=leave.created_at).strftime('%Y/%m/%d %H:%M')
        
        # دریافت کد پرسنلی افراد
        user_personnel_code = '-'
        if leave.user and hasattr(leave.user, 'userprofile'):
            user_personnel_code = leave.user.userprofile.personnel_code or '-'
        
        replacement_personnel_code = '-'
        if leave.replacement_person and hasattr(leave.replacement_person, 'userprofile'):
            replacement_personnel_code = leave.replacement_person.userprofile.personnel_code or '-'
        
        approver_personnel_code = '-'
        if leave.final_approver:
            approver_personnel_code = leave.final_approver.personnel_code or '-'
        
        row_data = [
            idx - 1,
            leave.user.get_full_name() if leave.user else '-',
            user_personnel_code,
            leave.work_group or '-',
            leave_type_dict.get(leave.leave_type, leave.leave_type),
            shift_date_jalali,
            shift_type_dict.get(leave.shift_type, leave.shift_type),
            status_dict.get(leave.status, leave.status),
            leave.replacement_person.get_full_name() if leave.replacement_person else '-',
            replacement_personnel_code,
            leave.final_approver.user.get_full_name() if leave.final_approver else '-',
            approver_personnel_code,
            created_at_jalali,
            leave.description or '-'
        ]
        
        for col_num, value in enumerate(row_data, 1):
            cell = ws.cell(row=idx, column=col_num)
            cell.value = value
            cell.alignment = cell_alignment
            cell.border = border
            
            # رنگ‌بندی بر اساس وضعیت
            if col_num == 8:  # ستون وضعیت
                if leave.status == 'approved':
                    cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                elif leave.status == 'rejected':
                    cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
                elif leave.status in ['pending_replacement', 'pending_approval']:
                    cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
    
    # تنظیم عرض ستون‌ها
    column_widths = [8, 25, 12, 20, 15, 15, 12, 18, 25, 12, 25, 12, 20, 40]
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = width
    
    # تنظیم ارتفاع ردیف هدر
    ws.row_dimensions[1].height = 30
    
    # ذخیره در حافظه و ارسال
    from io import BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    # نام فایل با تاریخ شمسی
    now_jalali = jdatetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'leave_reports_{now_jalali}.xlsx'
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


# ============= جزئیات درخواست =============

@login_required
def leave_detail(request, leave_id):
    """صفحه جزئیات یک درخواست مرخصی"""
    
    leave_request = get_object_or_404(
        ShiftReport.objects.select_related(
            'user', 'replacement_person', 'final_approver', 'rejected_by', 'crate_by'
        ),
        id=leave_id
    )
    
    # بررسی دسترسی - فقط درخواست دهنده، جایگزین، مدیران و کسانی که دسترسی آرشیو دارند
    has_access = (
        leave_request.user == request.user or
        leave_request.replacement_person == request.user or
        leave_request.can_be_approved_by(request.user) or
        check_permission(request.user, 'leave_archive')
    )
    
    if not has_access:
        messages.error(request, 'شما دسترسی به مشاهده این درخواست را ندارید.')
        return redirect('leave_reports:my_inbox')
    
    # ثبت فعالیت
    log_user_activity(
        user=request.user,
        activity_type='view',
        description=f'مشاهده جزئیات درخواست مرخصی {leave_request.user.get_full_name()}',
        related_model='ShiftReport',
        related_object_id=leave_request.id,
        url=request.get_full_path(),
        request=request
    )
    
    # بررسی اینکه آیا کاربر می‌تواند این درخواست را تأیید کند
    can_approve = leave_request.can_be_approved_by(request.user)
    
    return render(request, 'leave_reports/leave_detail.html', {
        'leave': leave_request,
        'page_title': 'جزئیات درخواست مرخصی',
        'can_approve': can_approve,
    })


# ============= مدیریت تأیید کنندگان (فقط سوپریوزر) =============

@login_required
def manage_approvers(request):
    """صفحه مدیریت سلسله مراتب تأیید"""
    
    # فقط سوپریوزر
    if not request.user.is_superuser:
        messages.error(request, 'فقط مدیر سیستم به این بخش دسترسی دارد.')
        return redirect('dashboard:dashboard')
    
    hierarchies = ApprovalHierarchy.objects.all().select_related(
        'section', 'part', 'approver', 'approver__user', 'approver__position'
    ).order_by('section__name', 'part__name')
    
    if request.method == 'POST':
        form = ApprovalHierarchyForm(request.POST)
        if form.is_valid():
            try:
                hierarchy = form.save()
                
                # ثبت فعالیت
                log_user_activity(
                    user=request.user,
                    activity_type='create',
                    description=f'تعریف تأیید کننده جدید: {hierarchy}',
                    related_model='ApprovalHierarchy',
                    related_object_id=hierarchy.id,
                    url=None,
                    request=request
                )
                
                messages.success(request, 'تأیید کننده با موفقیت ثبت شد.')
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success',
                        'message': 'تأیید کننده با موفقیت ثبت شد',
                        'hierarchy': {
                            'id': hierarchy.id,
                            'location': str(hierarchy),
                            'approver': str(hierarchy.approver)
                        }
                    })
                
                return redirect('leave_reports:manage_approvers')
                
            except Exception as e:
                messages.error(request, f'خطا در ثبت: {str(e)}')
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'error',
                        'message': str(e)
                    }, status=400)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'خطا در اعتبارسنجی فرم',
                    'errors': form.errors
                }, status=400)
    else:
        form = ApprovalHierarchyForm()
    
    # ثبت فعالیت
    log_user_activity(
        user=request.user,
        activity_type='view',
        description='مشاهده صفحه مدیریت تأیید کنندگان',
        related_model='ApprovalHierarchy',
        related_object_id=None,
        url=reverse('leave_reports:manage_approvers'),
        request=request
    )
    
    # Get sections for dropdown
    from accounts.models import Section
    sections = Section.objects.all().order_by('name')
    
    return render(request, 'leave_reports/manage_approvers.html', {
        'form': form,
        'hierarchies': hierarchies,
        'sections': sections,
        'page_title': 'مدیریت تأیید کنندگان',
    })


@login_required
def delete_approver(request, hierarchy_id):
    """حذف یک تأیید کننده"""
    
    # فقط سوپریوزر
    if not request.user.is_superuser:
        return JsonResponse({
            'status': 'error',
            'message': 'شما دسترسی به این عملیات را ندارید'
        }, status=403)
    
    hierarchy = get_object_or_404(ApprovalHierarchy, id=hierarchy_id)
    
    if request.method == 'POST':
        try:
            hierarchy_str = str(hierarchy)
            hierarchy.delete()
            
            # ثبت فعالیت
            log_user_activity(
                user=request.user,
                activity_type='delete',
                description=f'حذف تأیید کننده: {hierarchy_str}',
                related_model='ApprovalHierarchy',
                related_object_id=hierarchy_id,
                url=None,
                request=request
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'تأیید کننده با موفقیت حذف شد'
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'خطا در حذف: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'متد درخواست نامعتبر است'
    }, status=405)


# ============= API برای Select2 =============

@login_required
def api_get_users_for_replacement(request):
    """API برای دریافت لیست کاربران جهت انتخاب به عنوان جایگزین"""
    
    search = request.GET.get('q', '')
    
    users = User.objects.filter(is_active=True).exclude(id=request.user.id)
    
    # فیلتر براساس بخش کاربر فعلی
    if hasattr(request.user, 'userprofile') and request.user.userprofile.section:
        users = users.filter(userprofile__section=request.user.userprofile.section)
    
    # جستجو
    if search:
        users = users.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(userprofile__personnel_code__icontains=search)
        )
    
    users = users.select_related('userprofile')[:20]
    
    results = []
    for user in users:
        profile = getattr(user, 'userprofile', None)
        text = user.get_full_name() or user.username
        if profile and profile.personnel_code:
            text += f" ({profile.personnel_code})"
        
        results.append({
            'id': user.id,
            'text': text
        })
    
    return JsonResponse({
        'results': results,
        'pagination': {'more': False}
    })


@login_required
def api_get_parts_by_section(request):
    """API برای دریافت قسمت‌ها بر اساس بخش"""
    
    from accounts.models import Part
    
    section_id = request.GET.get('section_id')
    part_id = request.GET.get('part_id')  # برای استفاده در جاوااسکریپت
    
    if not section_id and not part_id:
        return JsonResponse({'results': [], 'pagination': {'more': False}})
    
    if section_id:
        parts = Part.objects.filter(section_id=section_id)
        results = [{'id': part.id, 'text': part.name} for part in parts]
    else:
        results = []
    
    return JsonResponse({
        'results': results,
        'pagination': {'more': False}
    })


@login_required
def api_get_unit_groups_by_part(request):
    """API برای دریافت گروه‌های واحد بر اساس قسمت"""
    import logging
    from accounts.models import UnitGroup
    
    logger = logging.getLogger(__name__)
    part_id = request.GET.get('part_id')
    
    logger.info(f"🔍 api_get_unit_groups_by_part called with part_id: {part_id}")
    
    if not part_id:
        logger.warning("⚠️ No part_id provided")
        return JsonResponse({'results': [], 'pagination': {'more': False}})
    
    try:
        unit_groups = UnitGroup.objects.filter(part_id=part_id)
        logger.info(f"📊 Found {unit_groups.count()} unit groups for part_id {part_id}")
        
        results = [{'id': unit_group.id, 'text': unit_group.name} for unit_group in unit_groups]
        logger.info(f"✅ Returning results: {results}")
        
        return JsonResponse({
            'results': results,
            'pagination': {'more': False}
        })
    except Exception as e:
        logger.error(f"❌ Error in api_get_unit_groups_by_part: {str(e)}", exc_info=True)
        return JsonResponse({'results': [], 'pagination': {'more': False}}, status=500)


@login_required
def api_get_positions_by_unit_group(request):
    """API برای دریافت سمت‌ها بر اساس گروه واحد"""
    
    from accounts.models import Position
    
    unit_group_id = request.GET.get('unit_group_id')
    
    if not unit_group_id:
        return JsonResponse({'results': [], 'pagination': {'more': False}})
    
    positions = Position.objects.filter(unit_group_id=unit_group_id)
    
    results = [{'id': position.id, 'text': position.name} for position in positions]
    
    return JsonResponse({
        'results': results,
        'pagination': {'more': False}
    })


@login_required
def api_get_user_profiles(request):
    """API برای جستجوی UserProfile ها برای تأیید کنندگان"""
    from accounts.models import UserProfile
    
    search_term = request.GET.get('q', '')
    page = int(request.GET.get('page', 1))
    page_size = 20
    
    # فیلتر UserProfile های فعال
    profiles = UserProfile.objects.filter(user__is_active=True).select_related('user', 'position', 'section', 'part')
    
    # جستجو
    if search_term:
        profiles = profiles.filter(
            Q(user__first_name__icontains=search_term) | 
            Q(user__last_name__icontains=search_term) |
            Q(user__username__icontains=search_term) |
            Q(personnel_code__icontains=search_term)
        )
    
    # Pagination
    start = (page - 1) * page_size
    end = start + page_size
    total_count = profiles.count()
    profiles_page = profiles[start:end]
    
    results = []
    for profile in profiles_page:
        full_name = profile.user.get_full_name() or profile.user.username
        
        # ساختن متن نمایشی
        parts_text = []
        if profile.position:
            parts_text.append(profile.position.name)
        if profile.section:
            parts_text.append(profile.section.name)
        if profile.personnel_code:
            parts_text.append(f"کد: {profile.personnel_code}")
        
        text = f"{full_name}"
        if parts_text:
            text += f" ({', '.join(parts_text)})"
        
        results.append({'id': profile.id, 'text': text})
    
    return JsonResponse({
        'results': results,
        'pagination': {'more': end < total_count}
    })


@login_required
def api_get_users_for_replacement(request):
    """API برای جستجوی کاربران برای انتخاب جایگزین"""
    
    search_term = request.GET.get('q', '')
    page = int(request.GET.get('page', 1))
    page_size = 20
    
    # فیلتر کاربران همان بخش کاربر
    users = User.objects.filter(is_active=True).exclude(id=request.user.id)
    
    if hasattr(request.user, 'userprofile') and request.user.userprofile.section:
        users = users.filter(userprofile__section=request.user.userprofile.section)
    
    # جستجو
    if search_term:
        users = users.filter(
            Q(first_name__icontains=search_term) | 
            Q(last_name__icontains=search_term) |
            Q(username__icontains=search_term)
        )
    
    # Pagination
    start = (page - 1) * page_size
    end = start + page_size
    total_count = users.count()
    users_page = users.select_related('userprofile')[start:end]
    
    results = []
    for user in users_page:
        full_name = user.get_full_name() or user.username
        position = user.userprofile.position.name if hasattr(user, 'userprofile') and user.userprofile.position else ''
        text = f"{full_name} ({position})" if position else full_name
        results.append({'id': user.id, 'text': text})
    
    return JsonResponse({
        'results': results,
        'pagination': {'more': end < total_count}
    })
