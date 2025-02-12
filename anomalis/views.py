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





name = 'anomalis'





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

    return render(request, 'anomalis/new-anomalie.html', {
        'form': form,
        'pagetitle': 'افزودن آنومالی جدید',
        'title': 'افزودن آنومالی جدید',
    })





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
    search_query = request.GET.get('search', '')
    priority_filter = request.GET.get('priority', 'همه')
    status_filter = request.GET.get('status', 'نا ایمن')
    time_filter = request.GET.get('time', 'همه')


    if request.user.groups.filter(name='مسئول پیگیری').exists():
        if request.user.groups.filter(name='مدیر HSE').exists():
            anomalies = Anomaly.objects.all().order_by('-created_at')
        else:
            user_profile = UserProfile.objects.get(user=request.user)
            anomalies = Anomaly.objects.filter(followup=user_profile)
    else:
        anomalies = Anomaly.objects.all().order_by('-created_at')

    # فیلتر جستجو
    if search_query:
        anomalies = anomalies.filter(
            Q(description__icontains=search_query) |
            Q(location__name__icontains=search_query) |
            Q(followup__user__first_name__icontains=search_query) |
            Q(created_by__user__first_name__icontains=search_query) |
            Q(created_by__user__last_name__icontains=search_query)|
            Q(followup__mobile__icontains=search_query)
        )

    # فیلتر اولویت
    if priority_filter != 'همه':
        anomalies = anomalies.filter(priority__priority=priority_filter)

    # فیلتر وضعیت
    if status_filter == 'ایمن':
        anomalies = anomalies.filter(action=True)
    elif status_filter == 'نا ایمن':
        anomalies = anomalies.filter(action=False)

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

        # محاسبه شروع ماه جاری
        start_of_month = jalali_now.replace(day=1).togregorian()

        # محاسبه پایان ماه جاری
        end_of_month = (jdatetime.date(jalali_now.year, jalali_now.month, 1) +
                        jdatetime.timedelta(days=31)).replace(day=1) - jdatetime.timedelta(days=1)
        end_of_month = end_of_month.togregorian()

        # تبدیل به datetime و افزودن منطقه زمانی
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

    # صفحه‌بندی
    paginator = Paginator(anomalies, 10)  # 10 آنومالی در هر صفحه
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)



    return render(request, 'anomalis/list.html', {
        'page_obj': page_obj,
        'anomalies': anomalies,
        'pagetitle': 'لیست آنومالی‌ها',
        'title': 'لیست آنومالی‌ها',
        'search_query': search_query,
        'priority_filter': priority_filter,
        'status_filter': status_filter,
        'time_filter': time_filter,
    })

#خذوجی اکسل


@login_required
@user_passes_test(lambda u: u.groups.filter(name='مدیر HSE').exists())
def export_anomalies_to_excel(request):
    search_query = request.GET.get('search', '')
    priority_filter = request.GET.get('priority', 'همه')
    status_filter = request.GET.get('status', 'همه')
    time_filter = request.GET.get('time', 'همه')

    anomalies = Anomaly.objects.all()

    # فیلتر جستجو
    if search_query:
        anomalies = anomalies.filter(
            Q(description__icontains=search_query) |
            Q(location__name__icontains=search_query) |
            Q(followup__user__first_name__icontains=search_query) |
            Q(created_by__user__first_name__icontains=search_query) |
            Q(created_by__user__last_name__icontains=search_query) |
            Q(followup__mobile__icontains=search_query)
        )

    # فیلتر اولویت
    if priority_filter != 'همه':
        anomalies = anomalies.filter(priority__priority=priority_filter)

    # فیلتر وضعیت
    if status_filter == 'ایمن':
        anomalies = anomalies.filter(action=True)
    elif status_filter == 'نا ایمن':
        anomalies = anomalies.filter(action=False)

    # فیلتر زمان (شمسی)
    if time_filter == 'امسال':
        jalali_now = jdatetime.date.today()
        start_of_year = jalali_now.replace(month=1, day=1).togregorian()
        end_of_year = jalali_now.replace(month=12, day=31).togregorian()

        anomalies = anomalies.filter(
            created_at__gte=make_aware(datetime.combine(start_of_year, datetime.min.time())),
            created_at__lte=make_aware(datetime.combine(end_of_year, datetime.max.time()))
        )
    elif time_filter == 'این ماه':
        jalali_now = jdatetime.date.today()
        start_of_month = jalali_now.replace(day=1).togregorian()
        end_of_month = (jdatetime.date(jalali_now.year, jalali_now.month, 1) +
                        jdatetime.timedelta(days=31)).replace(day=1) - jdatetime.timedelta(days=1)
        end_of_month = end_of_month.togregorian()

        anomalies = anomalies.filter(
            created_at__gte=make_aware(datetime.combine(start_of_month, datetime.min.time())),
            created_at__lte=make_aware(datetime.combine(end_of_month, datetime.max.time()))
        )
    elif time_filter == 'ماه گذشته':
        jalali_now = jdatetime.date.today()
        start_of_last_month = (jalali_now.replace(day=1) - jdatetime.timedelta(days=1)).replace(day=1).togregorian()
        end_of_last_month = (jalali_now.replace(day=1) - jdatetime.timedelta(days=1)).togregorian()

        anomalies = anomalies.filter(
            created_at__gte=make_aware(datetime.combine(start_of_last_month, datetime.min.time())),
            created_at__lte=make_aware(datetime.combine(end_of_last_month, datetime.max.time()))
        )
    elif time_filter == '90 روز اخیر':
        end_date = datetime.now()
        start_date = end_date - jdatetime.timedelta(days=90)

        anomalies = anomalies.filter(
            created_at__gte=make_aware(start_date),
            created_at__lte=make_aware(end_date)
        )

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

    # چک کردن اینکه آیا کاربر مدیر HSE است
    is_hse_manager = request.user.groups.filter(name__in=['مدیر HSE', 'افسر HSE']).exists()

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            try:
                # ذخیره کردن کامنت جدید
                comment = form.save(commit=False)
                comment.anomaly = anomaly
                comment.user = request.user.userprofile

                # بررسی اینکه آیا کامنت جواب به کامنت قبلی است
                parent_id = request.POST.get('parent_id')
                if parent_id:
                    parent_comment = get_object_or_404(Comment, id=parent_id)
                    comment.parent = parent_comment

                comment.save()

                # ارسال اعلان به مدیر HSE و ایجاد‌کننده آنومالی برای کامنت جدید
                if anomaly.created_by:
                    Notification.objects.create(
                        user=anomaly.created_by.user,
                        message=f"یک کامنت جدید برای آنومالی {anomaly.id} ارسال شد.",
                        url=reverse('anomalis:anomaly_detail', args=[anomaly.id])
                    )

                # ارسال اعلان به مدیران HSE
                hse_group = get(name='مدیر HSE')
                for user in hse_group.user_set.all():
                    Notification.objects.create(
                        user=user,
                        message=f"یک کامنت جدید برای آنومالی {anomaly.id} ارسال شد.",
                        url=reverse('anomalis:anomaly_detail', args=[anomaly.id])
                    )

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
                    {"Name": "shift", "Value": current_shift}
                ]
                send_template_sms(officer.mobile, template_id, parameters)
                messages.success(request, "پیامک با موفقیت به افسر ایمنی حاضر ارسال شد.")

                # ایجاد اعلان برای افسر ایمنی
                Notification.objects.create(
                    user=officer.user,
                    message=f"آنومالی {anomaly.id} در انتظار تأیید وضعیت ایمن است.",
                    url=reverse('anomalis:anomaly_detail', args=[anomaly.id])
                )
            else:
                messages.error(request, "افسر ایمنی حاضر یافت نشد.")
        except Exception as e:
            logger.error(f"خطا در ارسال پیامک: {str(e)}")
            messages.error(request, "خطا در ارسال پیامک.")

        return redirect('anomalis:anomaly_detail', pk=anomaly.pk)

    return redirect('anomalis:anomalis')




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

    context = {
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

    }

    return render(request, 'anomalis/reports.html', context)


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

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=anomalies_report.xlsx'
    wb.save(response)
    return response