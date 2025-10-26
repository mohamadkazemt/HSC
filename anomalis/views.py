from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.template.defaultfilters import title
from django.urls import reverse
from HSCprojects import settings
from dashboard.models import Notification
from dashboard.sms_utils import send_template_sms, logger
from permissions.utils import permission_required
from .forms import AnomalyForm, CommentForm
from .models import AnomalyDescription, CorrectiveAction, Comment, LocationSection, Anomaly, Location
from django.views.decorators.csrf import csrf_exempt
import jdatetime
from accounts.models import UserProfile
from django.contrib.auth.models import Group, User
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Prefetch
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncDate, ExtractMonth, ExtractYear
from django.http import HttpResponse, JsonResponse
import openpyxl
from .templatetags.jalali import to_jalali
from django.template.loader import get_template
from weasyprint import HTML
from django.conf import settings
from urllib.parse import urljoin
import logging
from shift_manager.utils import get_current_shift_and_group
from django.utils.timezone import make_aware
from datetime import datetime
from django.db.models import IntegerField
from django.db.models.functions import Cast
from .forms import AnomalyReportForm
from django.shortcuts import render
from django.db.models import Count, Q, F, CharField, Value
from django.db.models.functions import Concat
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from jalali_date import datetime2jalali
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required, user_passes_test
import jdatetime
from .models import Anomaly, UserProfile
import openpyxl
from rest_framework.decorators import api_view  # Correct import
from rest_framework.response import Response    # Correct import






name = 'anomalis'


def filter_anomalies(request, base_queryset):
    """
    تابع کمکی برای فیلتر و جستجو در آنومالی‌ها
    
    Args:
        request: شیء درخواست HTTP
        base_queryset: کوئری‌ست پایه برای فیلتر کردن
    
    Returns:
        tuple: (queryset فیلتر شده، دیکشنری مقادیر فیلتر)
    """
    # دریافت پارامترهای فیلتر
    search_query = request.GET.get('search', '')
    priority_filter = request.GET.get('priority', 'همه')
    status_filter = request.GET.get('status', 'همه')  # تغییر به 'همه' به عنوان پیش‌فرض
    time_filter = request.GET.get('time', 'همه')
    
    anomalies = base_queryset
    
    # فیلتر جستجو با قابلیت‌های بهبود یافته
    if search_query:
        # ساخت کوئری Q برای جستجو
        search_conditions = Q(description__icontains=search_query) | \
                          Q(location__name__icontains=search_query) | \
                          Q(followup__mobile__icontains=search_query) | \
                          Q(anomalydescription__description__icontains=search_query)
        
        # جستجو بر اساس ID اگر عدد باشد
        if search_query.isdigit():
            search_conditions |= Q(id=int(search_query))
        
        # جستجو بر اساس نام کامل (first_name + last_name) برای followup و created_by
        anomalies = anomalies.annotate(
            followup_full_name=Concat(
                'followup__user__first_name', 
                Value(' '), 
                'followup__user__last_name',
                output_field=CharField()
            ),
            creator_full_name=Concat(
                'created_by__user__first_name',
                Value(' '),
                'created_by__user__last_name',
                output_field=CharField()
            )
        )
        
        search_conditions |= Q(followup_full_name__icontains=search_query) | \
                           Q(creator_full_name__icontains=search_query) | \
                           Q(followup__user__first_name__icontains=search_query) | \
                           Q(created_by__user__first_name__icontains=search_query) | \
                           Q(created_by__user__last_name__icontains=search_query)
        
        anomalies = anomalies.filter(search_conditions)
    
    # فیلتر اولویت
    if priority_filter != 'همه':
        anomalies = anomalies.filter(priority__priority=priority_filter)
    
    # فیلتر وضعیت
    if status_filter == 'ایمن':
        anomalies = anomalies.filter(action=True)
    elif status_filter == 'نا ایمن':
        anomalies = anomalies.filter(action=False)
    # اگر 'همه' باشد، فیلتری اعمال نمی‌شود
    
    # فیلتر زمان
    if time_filter == 'امسال':
        jalali_now = jdatetime.date.today()
        start_of_year = jalali_now.replace(month=1, day=1).togregorian()
        end_of_year = jalali_now.replace(month=12, day=31).togregorian()
        
        start_of_year_aware = make_aware(datetime.combine(start_of_year, datetime.min.time()))
        end_of_year_aware = make_aware(datetime.combine(end_of_year, datetime.max.time()))
        
        anomalies = anomalies.filter(
            created_at__gte=start_of_year_aware,
            created_at__lte=end_of_year_aware
        )
    elif time_filter == 'این ماه':
        jalali_now = jdatetime.date.today()
        start_of_month = jalali_now.replace(day=1).togregorian()
        end_of_month = (jdatetime.date(jalali_now.year, jalali_now.month, 1) +
                        jdatetime.timedelta(days=31)).replace(day=1) - jdatetime.timedelta(days=1)
        end_of_month = end_of_month.togregorian()
        
        start_of_month_aware = make_aware(datetime.combine(start_of_month, datetime.min.time()))
        end_of_month_aware = make_aware(datetime.combine(end_of_month, datetime.max.time()))
        
        anomalies = anomalies.filter(
            created_at__gte=start_of_month_aware,
            created_at__lte=end_of_month_aware
        )
    elif time_filter == 'ماه گذشته':
        jalali_now = jdatetime.date.today()
        start_of_last_month_jalali = (jalali_now.replace(day=1) - jdatetime.timedelta(days=1)).replace(day=1)
        end_of_last_month_jalali = jalali_now.replace(day=1) - jdatetime.timedelta(days=1)
        
        start_of_last_month = start_of_last_month_jalali.togregorian()
        end_of_last_month = end_of_last_month_jalali.togregorian()
        
        start_of_last_month_aware = make_aware(datetime.combine(start_of_last_month, datetime.min.time()))
        end_of_last_month_aware = make_aware(datetime.combine(end_of_last_month, datetime.max.time()))
        
        anomalies = anomalies.filter(
            created_at__gte=start_of_last_month_aware,
            created_at__lte=end_of_last_month_aware
        )
    elif time_filter == '90 روز اخیر':
        end_date = datetime.now()
        start_date = end_date - jdatetime.timedelta(days=90)
        start_date_aware = make_aware(start_date)
        end_date_aware = make_aware(end_date)
        
        anomalies = anomalies.filter(
            created_at__gte=start_date_aware,
            created_at__lte=end_date_aware
        )
    
    # دیکشنری مقادیر فیلتر برای استفاده در context
    filter_context = {
        'search_query': search_query,
        'priority_filter': priority_filter,
        'status_filter': status_filter,
        'time_filter': time_filter,
    }
    
    return anomalies, filter_context


logger = logging.getLogger('anomalis')  # لاگر اختصاصی برای اپلیکیشن


@permission_required("anomalis")
@login_required
def anomalis(request):
    if request.method == 'POST':
        logger.info(f"Received POST request from user {request.user.username}")

        form = AnomalyForm(request.POST, request.FILES)
        if form.is_valid():
            logger.info(f"Form data is valid for user {request.user.username}")

            try:
                anomaly = form.save(commit=False)
                logger.debug(f"Anomaly instance created but not saved yet: {anomaly}")

                try:
                    user_profile = UserProfile.objects.get(user=request.user)
                    logger.debug(f"UserProfile found for user {request.user.username}: {user_profile}")
                except UserProfile.DoesNotExist:
                    logger.warning(f"UserProfile not found for user {request.user.username}")
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'status': 'error',
                            'message': 'پروفایل کاربری یافت نشد',
                            'redirect': reverse('accounts:login')
                        })
                    messages.error(request, 'پروفایل کاربری یافت نشد')
                    return redirect('accounts:login')

                # تنظیم مقادیر اضافی
                anomaly.created_by = user_profile
                anomaly.group = request.user.userprofile.group
                anomaly.hse_type = anomaly.anomalydescription.hse_type
                anomaly.save()
                logger.info(f"Anomaly {anomaly.id} saved successfully by user {request.user.username}")

                # ثبت فعالیت کاربر برای ایجاد آنومالی
                from dashboard.utils import log_user_activity
                log_user_activity(
                    user=request.user,
                    activity_type='create',
                    description=f'ایجاد آنومالی جدید با شناسه {anomaly.id}',
                    related_model='Anomaly',
                    related_object_id=anomaly.id,
                    url=reverse('anomalis:anomaly_detail', args=[anomaly.id]),
                    request=request
                )

                # ارسال پیامک به مسئول پیگیری
                template_id = 684430  # شناسه قالب
                try:
                    followup_user = anomaly.followup
                    profile = followup_user
                    parameters = [
                        {"Name": "status", "Value": "ثبت شده"},
                        {"Name": "anomaly_id", "Value": str(anomaly.id)}
                    ]
                    send_template_sms(profile.mobile, template_id, parameters)
                    logger.info(f"SMS sent to {profile.mobile} for anomaly {anomaly.id}")
                except Exception as sms_error:
                    logger.error(f"Error while sending SMS for anomaly {anomaly.id}: {sms_error}")

                # ایجاد اعلان برای مسئول پیگیری
                if anomaly.followup and anomaly.followup.user:
                    logger.debug(f"Attempting to create notification for user: {anomaly.followup.user.username}")
                    Notification.objects.create(
                        user=anomaly.followup.user,
                        message=f"آنومالی جدید با شناسه {anomaly.id} برای شما ثبت شد.",
                        url=reverse('anomalis:anomaly_detail', args=[anomaly.id])
                    )
                    logger.debug(f"Notification created successfully for user: {anomaly.followup.user.username}")
                else:
                    logger.warning("Followup user or user object is missing for anomaly. Skipping notification.")


                try:
                    hse_group = Group.objects.get(name='مدیر HSE')
                except Group.DoesNotExist:
                    logger.error("Group 'مدیر HSE' does not exist.")
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'status': 'error',
                            'message': 'گروه مدیر HSE یافت نشد',
                        })
                    messages.error(request, 'گروه مدیر HSE یافت نشد')
                    return redirect('anomalis:anomalis')


                for user in hse_group.user_set.all():
                    logger.debug(f"Attempting to create notification for HSE manager: {user.username}")
                    Notification.objects.create(
                        user=user,
                        message=f"آنومالی جدید با شناسه {anomaly.id} ثبت شد.",
                        url=reverse('anomalis:anomaly_detail', args=[anomaly.id])
                    )
                    logger.debug(f"Notification created successfully for HSE manager: {user.username}")


                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    logger.info(f"Returning success response for AJAX request by user {request.user.username}")
                    return JsonResponse({
                        'status': 'success',
                        'message': 'آنومالی با موفقیت ثبت شد',
                        'redirect': reverse('anomalis:anomalis')
                    })

                messages.success(request, 'آنومالی با موفقیت ثبت شد')
                return redirect('anomalis:anomalis')

            except Exception as e:
                logger.error(f"Error occurred while saving anomaly: {e}", exc_info=True)
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'error',
                        'message': f'خطا در ثبت آنومالی: {str(e)}',
                        'errors': {}
                    })
                messages.error(request, f'خطا در ثبت آنومالی: {str(e)}')
        else:
            logger.warning(f"Form validation failed for user {request.user.username}: {form.errors}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'فرم نامعتبر است',
                    'errors': form.errors
                })
            messages.error(request, 'فرم نامعتبر است. لطفاً مقادیر را به درستی وارد کنید')
    else:
        logger.info(f"GET request received from user {request.user.username}")
        form = AnomalyForm()
        
        # ثبت فعالیت مشاهده فرم ایجاد آنومالی
        from dashboard.utils import log_user_activity
        log_user_activity(
            user=request.user,
            activity_type='view',
            description='مشاهده فرم ایجاد آنومالی جدید',
            related_model='Anomaly',
            url=reverse('anomalis:anomalis'),
            request=request
        )

    # Get base anomaly queryset
    if request.user.groups.filter(name='مسئول پیگیری').exists():
        if request.user.groups.filter(name='مدیر HSE').exists():
            base_queryset = Anomaly.objects.all().order_by('-created_at')
        else:
            user_profile = UserProfile.objects.get(user=request.user)
            base_queryset = Anomaly.objects.filter(followup=user_profile).order_by('-created_at')
    else:
        base_queryset = Anomaly.objects.all().order_by('-created_at')
    
    # Apply filters using the helper function
    anomalies, filter_context = filter_anomalies(request, base_queryset)

    # Pagination
    paginator = Paginator(anomalies, 10)  # 10 anomalies per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'form': form,
        'pagetitle': 'افزودن آنومالی جدید',
        'title': 'افزودن آنومالی جدید',
        'page_obj': page_obj,
        'anomalies': anomalies,
    }
    context.update(filter_context)
    
    return render(request, 'anomalis/new-anomalie.html', context)





@permission_required("get_anomalydescription")

def get_anomalydescription(request):
    anomalytype_id = request.GET.get('anomalytype_id')
    descriptions = AnomalyDescription.objects.filter(anomalytype_id=anomalytype_id)
    descriptions_list = list(descriptions.values('id', 'description'))
    return JsonResponse({'descriptions': descriptions_list})


def get_hse_type(request, description_id):
    try:
        anomaly_description = AnomalyDescription.objects.get(id=description_id)
        return JsonResponse({'hse_type': anomaly_description.hse_type})
    except AnomalyDescription.DoesNotExist:
        return JsonResponse({'error': 'Description not found'}, status=404)


def get_corrective_action(request, description_id):
    try:
        corrective_actions = CorrectiveAction.objects.filter(anomali_type_id=description_id)
        actions_list = list(corrective_actions.values('id', 'description'))
        return JsonResponse({'actions': actions_list})
    except CorrectiveAction.DoesNotExist:
        return JsonResponse({'error': 'Corrective action not found'}, status=404)





@permission_required("list")

@login_required
def anomaly_list(request):
    # Get base anomaly queryset
    if request.user.groups.filter(name='مسئول پیگیری').exists():
        if request.user.groups.filter(name='مدیر HSE').exists():
            base_queryset = Anomaly.objects.all().order_by('-created_at')
        else:
            user_profile = UserProfile.objects.get(user=request.user)
            base_queryset = Anomaly.objects.filter(followup=user_profile).order_by('-created_at')
    else:
        base_queryset = Anomaly.objects.all().order_by('-created_at')
    
    # Apply filters using the helper function
    anomalies, filter_context = filter_anomalies(request, base_queryset)

    # صفحه‌بندی
    paginator = Paginator(anomalies, 10)  # 10 آنومالی در هر صفحه
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'anomalies': anomalies,
        'pagetitle': 'لیست آنومالی‌ها',
        'title': 'لیست آنومالی‌ها',
    }
    context.update(filter_context)

    return render(request, 'anomalis/list.html', context)

#خذوجی اکسل


@login_required
@user_passes_test(lambda u: u.groups.filter(name='مدیر HSE').exists())
def export_anomalies_to_excel(request):
    # Get base anomaly queryset
    base_queryset = Anomaly.objects.all()
    
    # Apply filters using the helper function
    anomalies, filter_context = filter_anomalies(request, base_queryset)

    # ایجاد فایل اکسل
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Anomalies"

    # اضافه کردن سرفصل‌ها
    ws.append(['کد آنومالی', 'مسئول پیگیری', 'ایجاد کننده', 'تاریخ', 'سایت', 'محل شناسایی آنومالی', 'شرح', 'اولویت', 'وضعیت'])

    # اضافه کردن داده‌ها
    for anomaly in anomalies:
        jalali_date = jdatetime.datetime.fromgregorian(datetime=anomaly.created_at).strftime('%Y/%m/%d')

        ws.append([
            anomaly.id,
            f"{anomaly.followup.user.first_name} {anomaly.followup.user.last_name}" if anomaly.followup else '',
            f"{anomaly.created_by.user.first_name} {anomaly.created_by.user.last_name}" if anomaly.created_by else '',
            jalali_date,
            anomaly.location.name if anomaly.location else '',
            anomaly.section.section if anomaly.section else '',
            anomaly.description,
            anomaly.priority.priority if anomaly.priority else 'نامشخص',
            'ایمن' if anomaly.action else 'نا ایمن',
        ])

    # تنظیم پاسخ HTTP برای دانلود فایل
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=anomalies.xlsx'
    wb.save(response)
    return response




@permission_required("anomaly_detail")
@login_required
def anomaly_detail_view(request, pk):
    anomaly = get_object_or_404(
        Anomaly.objects.prefetch_related(
            Prefetch('comments',
                     queryset=Comment.objects.filter(parent__isnull=True).select_related('user'),
                     to_attr='root_comments')
        ),
        pk=pk
    )

    # ثبت فعالیت مشاهده جزئیات آنومالی
    from dashboard.utils import log_user_activity
    log_user_activity(
        user=request.user,
        activity_type='view',
        description=f'مشاهده جزئیات آنومالی با شناسه {anomaly.id}',
        related_model='Anomaly',
        related_object_id=anomaly.id,
        url=reverse('anomalis:anomaly_detail', args=[anomaly.id]),
        request=request
    )

    # چک کردن اینکه آیا کاربر مدیر HSE است
    is_hse_manager = request.user.groups.filter(name__in=['مدیر HSE', 'افسر HSE']).exists()

    if request.method == "POST":
        form = CommentForm(request.POST, request.FILES)  # Pass request.FILES
        if form.is_valid():
            try:
                # ذخیره کردن کامنت جدید
                comment = form.save(commit=False)
                comment.anomaly = anomaly
                comment.user = request.user.userprofile

                # Associate the uploaded file
                comment.file = form.cleaned_data['file']  # Get the file from the form

                # بررسی اینکه آیا کامنت جواب به کامنت قبلی است
                parent_id = request.POST.get('parent_id')
                if parent_id:
                    parent_comment = get_object_or_404(Comment, id=parent_id)
                    comment.parent = parent_comment

                comment.save()
                
                # ثبت فعالیت ارسال کامنت
                log_user_activity(
                    user=request.user,
                    activity_type='create',
                    description=f'ارسال کامنت برای آنومالی با شناسه {anomaly.id}',
                    related_model='Comment',
                    related_object_id=comment.id,
                    url=reverse('anomalis:anomaly_detail', args=[anomaly.id]),
                    request=request
                )

                # ارسال اعلان به مدیر HSE و ایجاد‌کننده آنومالی برای کامنت جدید
                if anomaly.created_by:
                    Notification.objects.create(
                        user=anomaly.created_by.user,
                        message=f"یک کامنت جدید برای آنومالی {anomaly.id} ارسال شد.",
                        url=reverse('anomalis:anomaly_detail', args=[anomaly.id])
                    )

                # ارسال اعلان به مدیران HSE
                try:
                    hse_group = Group.objects.get(name='مدیر HSE')  # Corrected line
                    for user in hse_group.user_set.all():
                        Notification.objects.create(
                            user=user,
                            message=f"یک کامنت جدید برای آنومالی {anomaly.id} ارسال شد.",
                            url=reverse('anomalis:anomaly_detail', args=[anomaly.id])
                        )
                except Group.DoesNotExist:
                   logger.error("Group 'مدیر HSE' does not exist.")
                   messages.error(request, "گروه 'مدیر HSE' یافت نشد.")

                # اگر کامنت یک پاسخ باشد، ارسال اعلان به نویسنده کامنت قبلی
                if parent_id:
                    parent_comment_user = parent_comment.user
                    Notification.objects.create(
                        user=parent_comment_user.user,
                        message=f"پاسخی به کامنت شما در آنومالی {anomaly.id} ارسال شد.",
                        url=reverse('anomalis:anomaly_detail', args=[anomaly.id])
                    )

                messages.success(request, "نظر شما با موفقیت ثبت شد")

            except UserProfile.DoesNotExist:
                messages.error(request, "پروفایل کاربری یافت نشد")
                return redirect('accounts:profile')

        return redirect('anomalis:anomaly_detail', pk=anomaly.id)

    context = {
        'anomaly': anomaly,
        'comments': anomaly.root_comments,
        'form': CommentForm(),
        'title': 'جزئیات آنومالی',
        'is_hse_manager': is_hse_manager,
        'is_request_sent': anomaly.is_request_sent
    }

    return render(request, 'anomalis/anomaly-details.html', context)


@login_required
def request_safe(request, pk):
    anomaly = get_object_or_404(Anomaly, pk=pk)

    if request.method == 'POST' and request.user == anomaly.followup.user:
        anomaly.action = False
        anomaly.is_request_sent = True
        anomaly.requested_by = request.user  # ذخیره کاربر درخواست‌دهنده
        anomaly.save()
        
        # ثبت فعالیت درخواست ایمن‌سازی
        from dashboard.utils import log_user_activity
        log_user_activity(
            user=request.user,
            activity_type='update',
            description=f'درخواست ایمن‌سازی برای آنومالی با شناسه {anomaly.id}',
            related_model='Anomaly',
            related_object_id=anomaly.id,
            url=reverse('anomalis:anomaly_detail', args=[anomaly.id]),
            request=request
        )

        # شناسایی شیفت جاری و گروه مرتبط
        current_shift, group = get_current_shift_and_group()
        if not current_shift or not group:
            messages.error(request, "شیفت یا گروه کاری مرتبط یافت نشد.")
            return redirect('anomalis:anomaly_detail', pk=anomaly.pk)

        # یافتن افسر ایمنی حاضر در گروه و شیفت فعلی
        try:
            officer = UserProfile.objects.filter(group=group, user__groups__name='افسر HSE').first()
            if officer and officer.mobile:
                # ارسال پیامک به افسر ایمنی حاضر
                template_id = 254988  # شناسه قالب پیامک
                parameters = [
                    {"Name": "status", "Value": "در انتظار تایید"},
                    {"Name": "anomaly_id", "Value": str(anomaly.id)},
                ]
                send_template_sms(officer.mobile, template_id, parameters)
                
                # ایجاد اعلان برای افسر ایمنی
                Notification.objects.create(
                    user=officer.user,
                    message=f"درخواست ایمن‌سازی برای آنومالی {anomaly.id} ارسال شد.",
                    url=reverse('anomalis:anomaly_detail', args=[anomaly.id])
                )
                
                messages.success(request, "درخواست ایمن‌سازی با موفقیت ارسال شد و به افسر ایمنی حاضر اطلاع داده شد.")
            else:
                messages.warning(request, "افسر ایمنی در شیفت فعلی یافت نشد یا شماره موبایل ندارد.")
        except Exception as e:
            logger.error(f"Error in request_safe: {e}")
            messages.error(request, "خطا در ارسال درخواست ایمن‌سازی.")
            
        return redirect('anomalis:anomaly_detail', pk=anomaly.pk)
    else:
        messages.error(request, "شما مجاز به انجام این عملیات نیستید.")
        return redirect('anomalis:anomaly_detail', pk=anomaly.pk)




@login_required
@user_passes_test(lambda u: u.groups.filter(name__in=['مدیر HSE', 'افسر HSE']).exists())
def approve_safe(request, pk):
    anomaly = get_object_or_404(Anomaly, pk=pk)

    if request.method == 'POST':
        anomaly.action = True
        anomaly.is_request_sent = False
        anomaly.approved_by = request.user  # ذخیره کاربر تأیید‌کننده
        anomaly.save()

        # ارسال پیامک به ایجادکننده و مسئول پیگیری
        recipients = [anomaly.followup]
        template_id = 244118  # شناسه قالب تایید ایمنی
        for recipient in recipients:
            parameters = [
                {"Name": "status", "Value": "ایمن شده"},
                {"Name": "anomaly_id", "Value": str(anomaly.id)}
            ]
            send_template_sms(recipient.mobile, template_id, parameters)

            # ایجاد اعلان
            Notification.objects.create(
                user=recipient.user,
                message=f"آنومالی {anomaly.id} به وضعیت ایمن تغییر یافت.",
                url=reverse('anomalis:anomaly_detail', args=[anomaly.id])
            )

        return redirect('anomalis:anomaly_detail', pk=anomaly.pk)




@login_required
@user_passes_test(lambda u: u.groups.filter(name__in=['مدیر HSE', 'افسر HSE']).exists())
def reject_safe(request, pk):
    anomaly = get_object_or_404(Anomaly, pk=pk)

    if request.method == 'POST':
        anomaly.is_request_sent = False
        anomaly.save()

        # ارسال پیامک به ایجادکننده و مسئول پیگیری
        recipients = [anomaly.followup]
        template_id = 320925  # شناسه قالب رد ایمنی
        for recipient in recipients:
            parameters = [
                {"Name": "status", "Value": "رد شده"},
                {"Name": "anomaly_id", "Value": str(anomaly.id)}
            ]
            send_template_sms(recipient.mobile, template_id, parameters)

            # ایجاد اعلان
            Notification.objects.create(
                user=recipient.user,
                message=f"درخواست ایمن بودن آنومالی {anomaly.id} رد شد.",
                url=reverse('anomalis:anomaly_detail', args=[anomaly.id])
            )

        return redirect('anomalis:anomaly_detail', pk=anomaly.pk)





def get_sections(request):
    location_id = request.GET.get('location_id')
    sections = LocationSection.objects.filter(location_id=location_id).values('id', 'section')
    return JsonResponse({'sections': list(sections)})








@permission_required("anomaly_pdf")
@login_required
def anomaly_pdf_view(request, pk):
    anomaly = get_object_or_404(Anomaly, pk=pk)
    template = get_template('anomalis/detail_view.html')

    # ایجاد مسیر کامل فایل‌های استاتیک و مدیا
    static_url = request.build_absolute_uri(settings.STATIC_URL)
    media_url = request.build_absolute_uri(settings.MEDIA_URL)

    # رندر کردن HTML
    html_content = template.render({
        'anomaly': anomaly,
        'title': 'گزارش آنومالی',
        'static_url': static_url,
        'media_url': media_url,
    }, request)

    # ایجاد فایل PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="anomaly_{pk}.pdf"'

    # اضافه کردن base_url برای دسترسی به فایل‌های رسانه‌ای
    HTML(string=html_content, base_url=request.build_absolute_uri('/')).write_pdf(response)

    return response




@permission_required("get_locations_ajax")
@login_required
def get_locations_ajax(request):
    locations = Location.objects.all().values("id", "name")
    return JsonResponse(list(locations), safe=False)

@permission_required("get_all_sections_ajax")
@login_required
def get_all_sections_ajax(request):
    sections = LocationSection.objects.all().values("id","section", "location_id")
    return JsonResponse(list(sections), safe=False)






@login_required
def anomaly_reports(request):
    form = AnomalyReportForm(request.GET)
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    start_date_gregorian = None
    end_date_gregorian = None

    if form.is_valid():
        start_date = None  # Initialize start_date
        end_date = None  # Initialize end_date
        try:
            if start_date_str:
                start_date = jdatetime.datetime.strptime(start_date_str, "%Y/%m/%d").date()
                start_date_gregorian = start_date.togregorian()
                print("start_date_gregorian:", start_date_gregorian)
            if end_date_str:
                end_date = jdatetime.datetime.strptime(end_date_str, "%Y/%m/%d").date()
                end_date_gregorian = end_date.togregorian()
                print("end_date_gregorian:", end_date_gregorian)

            if start_date and end_date and start_date > end_date:
                raise ValidationError("تاریخ شروع باید قبل از تاریخ پایان باشد.")
        except ValueError:
            form.add_error(None, "فرمت تاریخ وارد شده صحیح نیست. لطفا از فرمت YYYY/MM/DD استفاده کنید.")
        except ValidationError as e:
            form.add_error(None, str(e))

    anomalies = Anomaly.objects.all()

    if start_date_gregorian:
        anomalies = anomalies.filter(created_at__date__gte=start_date_gregorian)

    if end_date_gregorian:
        anomalies = anomalies.filter(created_at__date__lte=end_date_gregorian)

    # Get ordering parameters for each tab
    tab = request.GET.get('tab', 'unit')  # Default tab

    order_by_unit = request.GET.get('order_by_unit', None)
    order_direction_unit = request.GET.get('direction_unit', 'asc')

    order_by_location = request.GET.get('order_by_location', None)
    order_direction_location = request.GET.get('direction_location', 'asc')

    order_by_shift = request.GET.get('order_by_shift', None)
    order_direction_shift = request.GET.get('direction_shift', 'asc')

    order_by_user = request.GET.get('order_by_user', None)
    order_direction_user = request.GET.get('direction_user', 'asc')

    order_by_description = request.GET.get('order_by_description', None)
    order_direction_description = request.GET.get('direction_description', 'asc')

    order_by_type = request.GET.get('order_by_type', None)
    order_direction_type = request.GET.get('direction_type', 'asc')

    # Helper function to apply ordering
    def apply_ordering(queryset, order_by, order_direction, valid_fields):
        if order_by in valid_fields:
            ordering = ('-' if order_direction == 'desc' else '') + order_by
            return queryset.order_by(ordering), order_by, order_direction
        return queryset, None, 'asc'

    # Apply ordering for each tab
    valid_unit_fields = ['unit', 'total', 'safe', 'unsafe']
    anomalies_by_unit, ordering_unit, order_direction_unit = apply_ordering(
        anomalies.values(unit=F('followup__section__name')).annotate(
            total=Count('id'),
            safe=Count('id', filter=Q(action=True)),
            unsafe=Count('id', filter=Q(action=False))
        ).distinct(),
        order_by_unit, order_direction_unit, valid_unit_fields
    )

    valid_location_fields = ['location__name', 'total', 'safe', 'unsafe']
    anomalies_by_location, ordering_location, order_direction_location = apply_ordering(
        anomalies.values('location__name').annotate(
            total=Count('id'),
            safe=Count('id', filter=Q(action=True)),
            unsafe=Count('id', filter=Q(action=False))
        ).distinct(),
        order_by_location, order_direction_location, valid_location_fields
    )

    valid_shift_fields = ['shift', 'total', 'safe', 'unsafe']
    anomalies_by_shift, ordering_shift, order_direction_shift = apply_ordering(
        anomalies.values(shift=F('created_by__group')).annotate(
            total=Count('id'),
            safe=Count('id', filter=Q(action=True)),
            unsafe=Count('id', filter=Q(action=False))
        ).distinct(),
        order_by_shift, order_direction_shift, valid_shift_fields
    )

    valid_user_fields = ['full_name', 'total', 'safe', 'unsafe']
    anomalies_by_user, ordering_user, order_direction_user = apply_ordering(
        anomalies.annotate(
            full_name=Concat('created_by__user__first_name', Value(' '), 'created_by__user__last_name',
                             output_field=CharField()),
            personnel_code=F('created_by__personnel_code')
        ).values('full_name', 'personnel_code').annotate(
            total=Count('id'),
            safe=Count('id', filter=Q(action=True)),
            unsafe=Count('id', filter=Q(action=False))
        ).distinct(),
        order_by_user, order_direction_user, valid_user_fields
    )

    valid_description_fields = ['anomalydescription__description', 'total', 'safe', 'unsafe']
    anomaly_frequency_by_description, ordering_description, order_direction_description = apply_ordering(
        anomalies.values('anomalydescription__description').annotate(
            total=Count('id'),
            safe=Count('id', filter=Q(action=True)),
            unsafe=Count('id', filter=Q(action=False))
        ).distinct(),
        order_by_description, order_direction_description, valid_description_fields
    )

    valid_type_fields = ['anomalytype__type', 'total']
    anomaly_count_by_type, ordering_type, order_direction_type = apply_ordering(
        anomalies.values('anomalytype__type').annotate(total=Count('id')),
        order_by_type, order_direction_type, valid_type_fields
    )

    # Most Frequent Anomaly by Description in each section
    sections = UserProfile.objects.values_list('section__name', flat=True).distinct()
    most_frequent_anomalies = {}
    for section in sections:
        most_frequent_anomaly = anomalies.filter(followup__section__name=section).values(
            'anomalydescription__description').annotate(total=Count('id')).order_by('-total').first()
        if most_frequent_anomaly:
            most_frequent_anomalies[section] = most_frequent_anomaly
        else:
            most_frequent_anomalies[section] = None

    # Most Cooperative Follow-up Officers
    followup_officers = UserProfile.objects.filter(user__groups__name='مسئول پیگیری',
                                                   followup_anomalies__isnull=False).annotate(
        total_anomalies=Count('followup_anomalies'),
        safe_anomalies=Count('followup_anomalies', filter=Q(followup_anomalies__action=True)),
        unsafe_anomalies=Count('followup_anomalies', filter=Q(followup_anomalies__action=False))
    ).order_by('-safe_anomalies')

    # Number of items per page
    items_per_page = request.GET.get('items_per_page', 10)
    try:
        items_per_page = int(items_per_page)
        if items_per_page <= 0:
            items_per_page = 10
    except ValueError:
        items_per_page = 10

    # Paginate data
    def paginate_data(queryset, items_per_page, page):
        paginator = Paginator(queryset, items_per_page)
        try:
            return paginator.page(page), paginator
        except (EmptyPage, InvalidPage):
            return paginator.page(1), paginator

    page_unit = request.GET.get('page_unit')
    anomalies_by_unit_paginated, paginator_unit = paginate_data(anomalies_by_unit, items_per_page, page_unit)

    page_location = request.GET.get('page_location')
    anomalies_by_location_paginated, paginator_location = paginate_data(anomalies_by_location, items_per_page,
                                                                        page_location)

    page_shift = request.GET.get('page_shift')
    anomalies_by_shift_paginated, paginator_shift = paginate_data(anomalies_by_shift, items_per_page, page_shift)

    page_user = request.GET.get('page_user')
    anomalies_by_user_paginated, paginator_user = paginate_data(anomalies_by_user, items_per_page, page_user)

    page_description = request.GET.get('page_description')
    anomaly_frequency_by_description_paginated, paginator_description = paginate_data(
        anomaly_frequency_by_description,
        items_per_page,
        page_description
    )

    # Calculate total anomaly for description tab and user
    total_anomalies = anomalies.count()

    # Calculate percentages for each item in anomalies_by_unit_paginated
    for item in anomalies_by_unit_paginated:
        total = item['total']
        item['safe_percentage'] = (item['safe'] / total) * 100 if total > 0 else 0
        item['unsafe_percentage'] = (item['unsafe'] / total) * 100 if total > 0 else 0

    # Calculate percentages for each item in anomalies_by_location_paginated
    for item in anomalies_by_location_paginated:
        total = item['total']
        item['safe_percentage'] = (item['safe'] / total) * 100 if total > 0 else 0
        item['unsafe_percentage'] = (item['unsafe'] / total) * 100 if total > 0 else 0

    # Calculate percentages for each item in anomalies_by_shift_paginated
    for item in anomalies_by_shift_paginated:
        total = item['total']
        item['safe_percentage'] = (item['safe'] / total) * 100 if total > 0 else 0
        item['unsafe_percentage'] = (item['unsafe'] / total) * 100 if total > 0 else 0

    # Calculate percentages for each item in anomalies_by_user_paginated
    for item in anomalies_by_user_paginated:
        total = item['total']
        item['safe_percentage'] = (item['safe'] / total) * 100 if total > 0 else 0
        item['unsafe_percentage'] = (item['unsafe'] / total) * 100 if total > 0 else 0
        item['total_percentage'] = (total / total_anomalies) * 100 if total_anomalies > 0 else 0

    # Calculate percentages for each item in anomaly_frequency_by_description_paginated
    for item in anomaly_frequency_by_description_paginated:
        total = item['total']
        item['safe_percentage'] = (item['safe'] / total) * 100 if total > 0 else 0
        item['unsafe_percentage'] = (item['unsafe'] / total) * 100 if total > 0 else 0
        item['total_percentage'] = (total / total_anomalies) * 100 if total_anomalies > 0 else 0

    # valid type
    valid_type_fields = ['anomalytype__type', 'total']
    anomaly_count_by_type, ordering_type, order_direction_type = apply_ordering(
        anomalies.values('anomalytype__type').annotate(total=Count('id')),
        order_by_type, order_direction_type, valid_type_fields
    )

    # Most Cooperative Follow-up Officers
    followup_officers = UserProfile.objects.filter(user__groups__name='مسئول پیگیری',
                                                   followup_anomalies__isnull=False).annotate(
        total_anomalies=Count('followup_anomalies'),
        safe_anomalies=Count('followup_anomalies', filter=Q(followup_anomalies__action=True)),
        unsafe_anomalies=Count('followup_anomalies', filter=Q(followup_anomalies__action=False))
    ).order_by('-safe_anomalies')

    # Chart Data and Options
    unit_chart_data = {
        'labels': [item['unit'] for item in anomalies_by_unit],
        'datasets': [
            {'label': 'مجموع', 'data': [item['total'] for item in anomalies_by_unit], 'backgroundColor': 'rgba(54, 162, 235, 0.5)'},
            {'label': 'ایمن', 'data': [item['safe'] for item in anomalies_by_unit], 'backgroundColor': 'rgba(75, 192, 192, 0.5)'},
            {'label': 'ناایمن', 'data': [item['unsafe'] for item in anomalies_by_unit], 'backgroundColor': 'rgba(255, 99, 132, 0.5)'},
        ]
    }
    unit_chart_options = {
        'scales': {'y': {'beginAtZero': True}},
        'responsive': True,
        'maintainAspectRatio': False,
    }

    location_chart_data = {
        'labels': [item['location__name'] for item in anomalies_by_location],
        'datasets': [
            {'label': 'مجموع', 'data': [item['total'] for item in anomalies_by_location], 'backgroundColor': 'rgba(54, 162, 235, 0.5)'},
            {'label': 'ایمن', 'data': [item['safe'] for item in anomalies_by_location], 'backgroundColor': 'rgba(75, 192, 192, 0.5)'},
            {'label': 'ناایمن', 'data': [item['unsafe'] for item in anomalies_by_location], 'backgroundColor': 'rgba(255, 99, 132, 0.5)'},
        ]
    }
    location_chart_options = {
        'scales': {'y': {'beginAtZero': True}},
        'responsive': True,
        'maintainAspectRatio': False,
    }

    shift_chart_data = {
    'labels': [item['shift'] for item in anomalies_by_shift],
    'datasets': [
        {'label': 'مجموع', 'data': [item['total'] for item in anomalies_by_shift], 'backgroundColor': 'rgba(54, 162, 235, 0.5)'},
        {'label': 'ایمن', 'data': [item['safe'] for item in anomalies_by_shift], 'backgroundColor': 'rgba(75, 192, 192, 0.5)'},
        {'label': 'ناایمن', 'data': [item['unsafe'] for item in anomalies_by_shift], 'backgroundColor': 'rgba(255, 99, 132, 0.5)'},
    ]
    }
    shift_chart_options = {
        'scales': {'y': {'beginAtZero': True}},
        'responsive': True,
        'maintainAspectRatio': False,
    }


    user_chart_data = {
        'labels': [f"{item['full_name']} ({item['personnel_code']})" for item in anomalies_by_user],
        'datasets': [
            {'label': 'مجموع', 'data': [item['total'] for item in anomalies_by_user], 'backgroundColor': 'rgba(54, 162, 235, 0.5)'},
            {'label': 'ایمن', 'data': [item['safe'] for item in anomalies_by_user], 'backgroundColor': 'rgba(75, 192, 192, 0.5)'},
            {'label': 'ناایمن', 'data': [item['unsafe'] for item in anomalies_by_user], 'backgroundColor': 'rgba(255, 99, 132, 0.5)'},
        ]
    }
    user_chart_options = {
        'scales': {'y': {'beginAtZero': True}},
        'responsive': True,
        'maintainAspectRatio': False,
    }


    description_chart_data = {
         'labels': [item['anomalydescription__description'] for item in anomaly_frequency_by_description],
        'datasets': [
            {'label': 'مجموع', 'data': [item['total'] for item in anomaly_frequency_by_description], 'backgroundColor': 'rgba(54, 162, 235, 0.5)'},
            {'label': 'ایمن', 'data': [item['safe'] for item in anomaly_frequency_by_description], 'backgroundColor': 'rgba(75, 192, 192, 0.5)'},
            {'label': 'ناایمن', 'data': [item['unsafe'] for item in anomaly_frequency_by_description], 'backgroundColor': 'rgba(255, 99, 132, 0.5)'},
        ]
    }
    description_chart_options = {
       'scales': {'y': {'beginAtZero': True}},
        'responsive': True,
        'maintainAspectRatio': False,
    }



    type_chart_data = {
        'labels': [item['anomalytype__type'] for item in anomaly_count_by_type],
        'datasets': [
            {'label': 'مجموع', 'data': [item['total'] for item in anomaly_count_by_type], 'backgroundColor':  'rgba(54, 162, 235, 0.5)'},
        ]
    }
    type_chart_options = {
        'scales': {'y': {'beginAtZero': True}},
        'responsive': True,
        'maintainAspectRatio': False,
    }
    most_cooperative_officer = followup_officers.first()

    context = {
        'title': 'تحیل گزارشات آنومالی',
        'tab': tab,
        'anomalies_by_unit_paginated': anomalies_by_unit_paginated,
        'ordering_unit': ordering_unit,
        'order_direction_unit': order_direction_unit,
        'anomalies_by_location_paginated': anomalies_by_location_paginated,
        'ordering_location': ordering_location,
        'order_direction_location': order_direction_location,
        'anomalies_by_shift_paginated': anomalies_by_shift_paginated,
        'ordering_shift': ordering_shift,
        'order_direction_shift': order_direction_shift,
        'anomalies_by_user_paginated': anomalies_by_user_paginated,
        'ordering_user': ordering_user,
        'order_direction_user': order_direction_user,
        'anomaly_frequency_by_description_paginated': anomaly_frequency_by_description_paginated,
        'ordering_description': ordering_description,
        'order_direction_description': order_direction_description,
        'anomaly_count_by_type': anomaly_count_by_type,
        'most_frequent_anomalies': most_frequent_anomalies,
        'followup_officers': followup_officers,
        'paginator_unit': Paginator(anomalies_by_unit, items_per_page),
        'paginator_location': Paginator(anomalies_by_location, items_per_page),
        'paginator_shift': Paginator(anomalies_by_shift, items_per_page),
        'paginator_user': Paginator(anomalies_by_user, items_per_page),
        'paginator_description': Paginator(anomaly_frequency_by_description, items_per_page),
        'form': form,
        'ordering_type': None,  # Default value for ordering_type
        'order_direction_type': 'asc',  # Default value for order_direction_type,

        'unit_chart_data': unit_chart_data,
        'location_chart_data': location_chart_data,
        'shift_chart_data': shift_chart_data,
        'user_chart_data': user_chart_data,
        'description_chart_data': description_chart_data,
        'type_chart_data': type_chart_data,
        'most_cooperative_officer': most_cooperative_officer,
        'unit_chart_options': unit_chart_options,
        'location_chart_options': location_chart_options,
        'shift_chart_options': shift_chart_options,
        'user_chart_options': user_chart_options,
        'description_chart_options': description_chart_options,
        'type_chart_options': type_chart_options,

    }

    return render(request, 'anomalis/reports.html', context)


@api_view(['GET'])
def anomaly_reports_api(request):
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    start_date_gregorian = None
    end_date_gregorian = None
    if start_date_str:
        start_date = jdatetime.datetime.strptime(start_date_str, "%Y/%m/%d").date()
        start_date_gregorian = start_date.togregorian()
    if end_date_str:
        end_date = jdatetime.datetime.strptime(end_date_str, "%Y/%m/%d").date()
        end_date_gregorian = end_date.togregorian()
    anomalies = Anomaly.objects.all()
    if start_date_gregorian:
        anomalies = anomalies.filter(created_at__date__gte=start_date_gregorian)
    if end_date_gregorian:
        anomalies = anomalies.filter(created_at__date__lte=end_date_gregorian)
    tab = request.GET.get('tab', 'unit') # We don't really *need* this for the API anymore.

    # --- Prepare data for all chart types (similar to anomaly_reports)---

    # Unit Data
    anomalies_by_unit = anomalies.values(unit=F('followup__section__name')).annotate(
        total=Count('id'),
        safe=Count('id', filter=Q(action=True)),
        unsafe=Count('id', filter=Q(action=False))
    ).distinct()

    # Location Data
    anomalies_by_location = anomalies.values('location__name').annotate(
        total=Count('id'),
        safe=Count('id', filter=Q(action=True)),
        unsafe=Count('id', filter=Q(action=False))
    ).distinct()

    # Shift Data
    anomalies_by_shift = anomalies.values(shift=F('created_by__group')).annotate(
        total=Count('id'),
        safe=Count('id', filter=Q(action=True)),
        unsafe=Count('id', filter=Q(action=False))
    ).distinct()

    # User Data
    anomalies_by_user = anomalies.annotate(
        full_name=Concat('created_by__user__first_name', Value(' '), 'created_by__user__last_name',
                            output_field=CharField()),
        personnel_code=F('created_by__personnel_code')
    ).values('full_name', 'personnel_code').annotate(
        total=Count('id'),
        safe=Count('id', filter=Q(action=True)),
        unsafe=Count('id', filter=Q(action=False))
    ).distinct()

    # Description Data
    anomaly_frequency_by_description = anomalies.values('anomalydescription__description').annotate(
        total=Count('id'),
        safe=Count('id', filter=Q(action=True)),
        unsafe=Count('id', filter=Q(action=False))
    ).distinct()

    # Type Data
    anomaly_count_by_type = anomalies.values('anomalytype__type').annotate(total=Count('id'))


    # Return ALL the data in a single, structured JSON response
    data = {
        'anomalies_by_unit': list(anomalies_by_unit),  # Correctly return lists
        'anomalies_by_location': list(anomalies_by_location),
        'anomalies_by_shift': list(anomalies_by_shift),
        'anomalies_by_user': list(anomalies_by_user),
        'anomaly_frequency_by_description': list(anomaly_frequency_by_description),
        'anomaly_count_by_type': list(anomaly_count_by_type),
    }
    return Response(data)  # Use rest_framework's Response


@login_required
@user_passes_test(lambda u: u.groups.filter(name='مدیر HSE').exists())
def export_report_to_excel(request):
    form = AnomalyReportForm(request.GET)
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    start_date_gregorian = None
    end_date_gregorian = None

    if form.is_valid():
        start_date = None  # Initialize start_date
        end_date = None  # Initialize end_date
        try:
            if start_date_str:
                start_date = jdatetime.datetime.strptime(start_date_str, "%Y/%m/%d").date()
                start_date_gregorian = start_date.togregorian()
                print("start_date_gregorian:", start_date_gregorian)
            if end_date_str:
                end_date = jdatetime.datetime.strptime(end_date_str, "%Y/%m/%d").date()
                end_date_gregorian = end_date.togregorian()
                print("end_date_gregorian:", end_date_gregorian)

            if start_date and end_date and start_date > end_date:
                raise ValidationError("تاریخ شروع باید قبل از تاریخ پایان باشد.")
        except ValueError:
            form.add_error(None, "فرمت تاریخ وارد شده صحیح نیست. لطفا از فرمت YYYY/MM/DD استفاده کنید.")
        except ValidationError as e:
            form.add_error(None, str(e))

    anomalies = Anomaly.objects.all()

    if start_date_gregorian:
        anomalies = anomalies.filter(created_at__date__gte=start_date_gregorian)

    if end_date_gregorian:
        anomalies = anomalies.filter(created_at__date__lte=end_date_gregorian)

    # Get ordering parameters for each tab
    tab = request.GET.get('tab', 'unit')  # Default tab

    order_by_unit = request.GET.get('order_by_unit', None)
    order_direction_unit = request.GET.get('direction_unit', 'asc')

    order_by_location = request.GET.get('order_by_location', None)
    order_direction_location = request.GET.get('direction_location', 'asc')

    order_by_shift = request.GET.get('order_by_shift', None)
    order_direction_shift = request.GET.get('direction_shift', 'asc')

    order_by_user = request.GET.get('order_by_user', None)
    order_direction_user = request.GET.get('direction_user', 'asc')

    order_by_description = request.GET.get('order_by_description', None)
    order_direction_description = request.GET.get('direction_description', 'asc')

    order_by_type = request.GET.get('order_by_type', None)
    order_direction_type = request.GET.get('direction_type', 'asc')

    # Helper function to apply ordering
    def apply_ordering(queryset, order_by, order_direction, valid_fields):
        if order_by in valid_fields:
            ordering = ('-' if order_direction == 'desc' else '') + order_by
            return queryset.order_by(ordering), order_by, order_direction
        return queryset, None, 'asc'

    # Apply ordering for each tab
    valid_unit_fields = ['unit', 'total', 'safe', 'unsafe']
    anomalies_by_unit, ordering_unit, order_direction_unit = apply_ordering(
        anomalies.values(unit=F('followup__section__name')).annotate(
            total=Count('id'),
            safe=Count('id', filter=Q(action=True)),
            unsafe=Count('id', filter=Q(action=False))
        ).distinct(),
        order_by_unit, order_direction_unit, valid_unit_fields
    )

    valid_location_fields = ['location__name', 'total', 'safe', 'unsafe']
    anomalies_by_location, ordering_location, order_direction_location = apply_ordering(
        anomalies.values('location__name').annotate(
            total=Count('id'),
            safe=Count('id', filter=Q(action=True)),
            unsafe=Count('id', filter=Q(action=False))
        ).distinct(),
        order_by_location, order_direction_location, valid_location_fields
    )

    valid_shift_fields = ['shift', 'total', 'safe', 'unsafe']
    anomalies_by_shift, ordering_shift, order_direction_shift = apply_ordering(
        anomalies.values(shift=F('created_by__group')).annotate(
            total=Count('id'),
            safe=Count('id', filter=Q(action=True)),
            unsafe=Count('id', filter=Q(action=False))
        ).distinct(),
        order_by_shift, order_direction_shift, valid_shift_fields
    )

    valid_user_fields = ['full_name', 'total', 'safe', 'unsafe']
    anomalies_by_user, ordering_user, order_direction_user = apply_ordering(
        anomalies.annotate(
            full_name=Concat('created_by__user__first_name', Value(' '), 'created_by__user__last_name',
                             output_field=CharField()),
            personnel_code=F('created_by__personnel_code')
        ).values('full_name', 'personnel_code').annotate(
            total=Count('id'),
            safe=Count('id', filter=Q(action=True)),
            unsafe=Count('id', filter=Q(action=False))
        ).distinct(),
        order_by_user, order_direction_user, valid_user_fields
    )

    valid_description_fields = ['anomalydescription__description', 'total', 'safe', 'unsafe']
    anomaly_frequency_by_description, ordering_description, order_direction_description = apply_ordering(
        anomalies.values('anomalydescription__description').annotate(
            total=Count('id'),
            safe=Count('id', filter=Q(action=True)),
            unsafe=Count('id', filter=Q(action=False))
        ).distinct(),
        order_by_description, order_direction_description, valid_description_fields
    )

    valid_type_fields = ['anomalytype__type', 'total']
    anomaly_count_by_type, ordering_type, order_direction_type = apply_ordering(
        anomalies.values('anomalytype__type').annotate(total=Count('id')),
        order_by_type, order_direction_type, valid_type_fields
    )

    # Most Frequent Anomaly by Description in each section
    sections = UserProfile.objects.values_list('section__name', flat=True).distinct()
    most_frequent_anomalies = {}
    for section in sections:
        most_frequent_anomaly = anomalies.filter(followup__section__name=section).values(
            'anomalydescription__description').annotate(total=Count('id')).order_by('-total').first()
        if most_frequent_anomaly:
            most_frequent_anomalies[section] = most_frequent_anomaly
        else:
            most_frequent_anomalies[section] = None

    # Most Cooperative Follow-up Officers
    followup_officers = UserProfile.objects.filter(user__groups__name='مسئول پیگیری',
                                                   followup_anomalies__isnull=False).annotate(
        total_anomalies=Count('followup_anomalies'),
        safe_anomalies=Count('followup_anomalies', filter=Q(followup_anomalies__action=True)),
        unsafe_anomalies=Count('followup_anomalies', filter=Q(followup_anomalies__action=False))
    ).order_by('-safe_anomalies')

    wb = openpyxl.Workbook()

    # Create a worksheet for each report type
    ws_unit = wb.create_sheet("گزارش واحد")
    ws_location = wb.create_sheet("گزارش موقعیت")
    ws_shift = wb.create_sheet("گزارش شیفت")
    ws_user = wb.create_sheet("گزارش کاربر")
    ws_description = wb.create_sheet("گزارش شرح")
    ws_type = wb.create_sheet("گزارش نوع")

    # Calculate percentages for each report type
    total_anomalies = anomalies.count()

    # Unit Report
    ws_unit.append(['واحد', 'مجموع', 'ایمن', 'ناایمن', 'درصد ایمنی', 'درصد ناایمنی'])
    for item in anomalies_by_unit:
        safe_percentage = (item['safe'] / item['total']) * 100 if item['total'] > 0 else 0
        unsafe_percentage = (item['unsafe'] / item['total']) * 100 if item['total'] > 0 else 0
        ws_unit.append([item['unit'], item['total'], item['safe'], item['unsafe'], safe_percentage, unsafe_percentage])

    # Location Report
    ws_location.append(['موقعیت', 'مجموع', 'ایمن', 'ناایمن', 'درصد ایمنی', 'درصد ناایمنی'])
    for item in anomalies_by_location:
        safe_percentage = (item['safe'] / item['total']) * 100 if item['total'] > 0 else 0
        unsafe_percentage = (item['unsafe'] / item['total']) * 100 if item['total'] > 0 else 0
        ws_location.append(
            [item['location__name'], item['total'], item['safe'], item['unsafe'], safe_percentage, unsafe_percentage])

    # Shift Report
    ws_shift.append(['شیفت', 'مجموع', 'ایمن', 'ناایمن', 'درصد ایمنی', 'درصد ناایمنی'])
    for item in anomalies_by_shift:
        safe_percentage = (item['safe'] / item['total']) * 100 if item['total'] > 0 else 0
        unsafe_percentage = (item['unsafe'] / item['total']) * 100 if item['total'] > 0 else 0
        ws_shift.append(
            [item['shift'], item['total'], item['safe'], item['unsafe'], safe_percentage, unsafe_percentage])

    # User Report
    ws_user.append(['نام کامل', 'کد پرسنلی', 'مجموع', 'ایمن', 'ناایمن', 'درصد ایمنی', 'درصد ناایمنی', 'درصد از کل'])
    for item in anomalies_by_user:
        safe_percentage = (item['safe'] / item['total']) * 100 if item['total'] > 0 else 0
        unsafe_percentage = (item['unsafe'] / item['total']) * 100 if item['total'] > 0 else 0
        total_percentage = (item['total'] / total_anomalies) * 100 if total_anomalies > 0 else 0
        ws_user.append(
            [item['full_name'], item['personnel_code'], item['total'], item['safe'], item['unsafe'], safe_percentage,
             unsafe_percentage, total_percentage])

    # Description Report
    ws_description.append(['شرح', 'مجموع', 'ایمن', 'ناایمن', 'درصد ایمنی', 'درصد ناایمنی', 'درصد از کل'])
    for item in anomaly_frequency_by_description:
        safe_percentage = (item['safe'] / item['total']) * 100 if item['total'] > 0 else 0
        unsafe_percentage = (item['unsafe'] / item['total']) * 100 if item['total'] > 0 else 0
        total_percentage = (item['total'] / total_anomalies) * 100 if total_anomalies > 0 else 0
        ws_description.append(
            [item['anomalydescription__description'], item['total'], item['safe'], item['unsafe'], safe_percentage,
             unsafe_percentage, total_percentage])

    # Type Report
    ws_type.append(['نوع', 'مجموع'])
    for item in anomaly_count_by_type:
        ws_type.append([item['anomalytype__type'], item['total']])

    # Determine filename
    if start_date_str and end_date_str:
        # Convert Gregorian dates to Jalali dates
        start_date_jalali = jdatetime.date.fromgregorian(date=start_date_gregorian).strftime("%Y/%m/%d")
        end_date_jalali = jdatetime.date.fromgregorian(date=end_date_gregorian).strftime("%Y/%m/%d")

        filename = f"report_{start_date_jalali}_to_{end_date_jalali}.xlsx"
    else:
        filename = "گزارش کلی.xlsx"

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    # Encode filename for UTF-8 compatibility
    filename_encoded = filename.encode('utf-8')
    response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{filename_encoded.decode("unicode_escape")}'

    wb.save(response)
    return response



