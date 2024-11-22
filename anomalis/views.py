from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.template.defaultfilters import title
from django.urls import reverse

from HSCprojects import settings
from dashboard.models import Notification
from dashboard.sms_utils import send_template_sms, logger
from .forms import AnomalyForm, CommentForm
from django.http import JsonResponse
from .models import AnomalyDescription, CorrectiveAction, Comment, LocationSection, Anomaly
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
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
import openpyxl
from .templatetags.jalali import to_jalali
from django.template.loader import get_template
from django.http import HttpResponse
from weasyprint import HTML
from django.conf import settings
from urllib.parse import urljoin
import logging
from shift_manager.utils import get_current_shift_and_group


name = 'anomalis'




# تنظیم لاگر
logger = logging.getLogger(__name__)

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

                # ارسال پیامک به مسئول پیگیری مرتبط با آنومالی
                template_id = 684430  # شناسه قالب
                try:
                    followup_user = anomaly.followup  # مسئول پیگیری مرتبط با آنومالی
                    profile = followup_user  # UserProfile کاربر مسئول پیگیری
                    parameters = [
                        {"Name": "status", "Value": "ثبت شده"},
                        {"Name": "anomaly_id", "Value": str(anomaly.id)}
                    ]
                    send_template_sms(profile.mobile, template_id, parameters)
                    logger.info(f"SMS sent to {profile.mobile} for anomaly {anomaly.id}")
                except UserProfile.DoesNotExist:
                    logger.warning(f"UserProfile not found for followup user of anomaly {anomaly.id}")

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
    else:
        logger.info(f"GET request received from user {request.user.username}")
        form = AnomalyForm()

    return render(request, 'anomalis/new-anomalie.html', {
        'form': form,
        'pagetitle': 'افزودن آنومالی جدید',
        'title': 'افزودن آنومالی جدید',
    })




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




@login_required
def anomaly_list(request):
    search_query = request.GET.get('search', '')
    priority_filter = request.GET.get('priority', 'همه')
    status_filter = request.GET.get('status', 'همه')
    time_filter = request.GET.get('time', 'همه')
    if request.user.groups.filter(name='مسئول پیگیری').exists():
        if request.user.groups.filter(name='مدیر HSE').exists():
            anomalies = Anomaly.objects.all().order_by('-created_at')
        else:
            user_profile = UserProfile.objects.get(user=request.user)
            anomalies = Anomaly.objects.filter(followup=user_profile)
    else:
        anomalies = Anomaly.objects.all().order_by('-created_at')

    # Convert the date fields to Jalali
    for anomaly in anomalies:
        anomaly.created_at_jalali = jdatetime.datetime.fromgregorian(datetime=anomaly.created_at)
        anomaly.updated_at_jalali = jdatetime.datetime.fromgregorian(datetime=anomaly.updated_at)

        # اعمال فیلتر جستجو (در صورت وجود عبارت جستجو)
    if search_query:
        anomalies = anomalies.filter(
            Q(description__icontains=search_query) |
            Q(location__name__icontains=search_query) |
            Q(followup__user__first_name__icontains=search_query) |
            Q(created_by__user__first_name__icontains=search_query) |
            Q(created_by__user__last_name__icontains=search_query)
        )

        # فیلتر اولویت (در صورت انتخاب اولویت خاص)
    if priority_filter != 'همه':
        anomalies = anomalies.filter(priority__priority=priority_filter)

        # فیلتر وضعیت (در صورت انتخاب وضعیت خاص)
    if status_filter == 'ایمن':
        anomalies = anomalies.filter(action=True)
    elif status_filter == 'نا ایمن':
        anomalies = anomalies.filter(action=False)

        # فیلتر زمان (در صورت انتخاب زمان خاص)
    if time_filter == 'امسال':
        anomalies = anomalies.filter(created_at__year=timezone.now().year)
    elif time_filter == 'این ماه':
        anomalies = anomalies.filter(created_at__month=timezone.now().month, created_at__year=timezone.now().year)
    elif time_filter == 'ماه گذشته':
        last_month = timezone.now().month - 1
        anomalies = anomalies.filter(created_at__month=last_month, created_at__year=timezone.now().year)
    elif time_filter == '90 روز اخیر':
        anomalies = anomalies.filter(created_at__gte=timezone.now() - timezone.timedelta(days=90))

    paginator = Paginator(anomalies, 10)  # 10 anomalies per page
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

    if search_query:
        anomalies = anomalies.filter(
            Q(description__icontains=search_query) |
            Q(location__name__icontains=search_query) |
            Q(followup__user__first_name__icontains=search_query) |
            Q(created_by__user__first_name__icontains=search_query) |
            Q(created_by__user__last_name__icontains=search_query)
        )

    if priority_filter != 'همه':
        anomalies = anomalies.filter(priority__priority=priority_filter)

    if status_filter == 'ایمن':
        anomalies = anomalies.filter(action=True)
    elif status_filter == 'نا ایمن':
        anomalies = anomalies.filter(action=False)

    if time_filter == 'امسال':
        anomalies = anomalies.filter(created_at__year=timezone.now().year)
    elif time_filter == 'این ماه':
        anomalies = anomalies.filter(created_at__month=timezone.now().month, created_at__year=timezone.now().year)
    elif time_filter == 'ماه گذشته':
        last_month = timezone.now().month - 1
        anomalies = anomalies.filter(created_at__month=last_month, created_at__year=timezone.now().year)
    elif time_filter == '90 روز اخیر':
        anomalies = anomalies.filter(created_at__gte=timezone.now() - timezone.timedelta(days=90))

    # ایجاد فایل اکسل
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Anomalies"

    # اضافه کردن سرفصل‌ها
    ws.append(['کد آنومالی', 'مسئول پیگیری', 'ایجاد کننده', 'تاریخ', 'سایت','محل شناسایی آنومالی', 'شرح', 'اولویت', 'وضعیت'])

    # اضافه کردن داده‌ها
    for anomaly in anomalies:
        jalali_date = to_jalali(anomaly.created_at)

        ws.append([
            anomaly.id,
            f"{anomaly.followup.user.first_name} {anomaly.followup.user.last_name}",
            f"{anomaly.created_by.user.first_name} {anomaly.created_by.user.last_name}",
            jalali_date,
            anomaly.location.name,
            anomaly.section.section,
            anomaly.description,
            anomaly.priority.priority,
            'ایمن' if anomaly.action else 'نا ایمن',
        ])

    # تنظیم پاسخ HTTP برای دانلود فایل
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=anomalies.xlsx'
    wb.save(response)
    return response







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

    # Remove permission check and just use login_required
    is_hse_manager = request.user.groups.filter(name__in=['مدیر HSE', 'افسر HSE']).exists()

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            try:
                comment = form.save(commit=False)
                comment.anomaly = anomaly
                comment.user = request.user.userprofile

                # Handle reply
                parent_id = request.POST.get('parent_id')
                if parent_id:
                    parent_comment = get_object_or_404(Comment, id=parent_id)
                    comment.parent = parent_comment

                comment.save()
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

        return redirect('anomalis:anomaly_detail', pk=anomaly.pk)




def get_sections(request):
    location_id = request.GET.get('location_id')
    sections = LocationSection.objects.filter(location_id=location_id).values('id', 'section')
    return JsonResponse({'sections': list(sections)})







@login_required
def anomaly_pdf_view(request, pk):
    anomaly = get_object_or_404(Anomaly, pk=pk)
    template = get_template('anomalis/detail_view.html')

    # ایجاد مسیر کامل فایل‌های استاتیک و مدیا
    static_url = request.build_absolute_uri(settings.STATIC_URL)
    media_url = request.build_absolute_uri(settings.MEDIA_URL)

    html_content = template.render({
        'anomaly': anomaly,
        'title': 'گزارش آنومالی',
        'static_url': static_url,
        'media_url': media_url,
    }, request)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="anomaly_{pk}.pdf"'
    HTML(string=html_content).write_pdf(response)
    return response

