from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.template.defaultfilters import title
from django.urls import reverse
from dashboard.models import Notification
from dashboard.sms_utils import send_template_sms, logger

from .forms import AnomalyForm, CommentForm
from django.http import JsonResponse
from .models import AnomalyDescription, CorrectiveAction, Comment
from .models import Anomaly
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

name = 'anomalis'


# views.py

# views.py

@login_required
def anomalis(request):
    if request.method == 'POST':
        form = AnomalyForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                anomaly = form.save(commit=False)

                try:
                    user_profile = UserProfile.objects.get(user=request.user)
                except UserProfile.DoesNotExist:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'status': 'error',
                            'message': 'پروفایل کاربری یافت نشد',
                            'redirect': reverse('accounts:login')
                        })
                    messages.error(request, 'پروفایل کاربری یافت نشد')
                    return redirect('accounts:login')

                anomaly.created_by = user_profile
                anomaly.group = request.user.userprofile.group
                anomaly.hse_type = anomaly.anomalydescription.hse_type
                anomaly.save()

                # ارسال پیامک به مسئولین پیگیری
                responsible_users = User.objects.filter(groups__name='مسئول پیگیری')
                template_id = 684430  # شناسه قالب
                for user in responsible_users:
                    try:
                        profile = UserProfile.objects.get(user=user)
                        parameters = [
                            {"Name": "status", "Value": "ثبت شده"},
                            {"Name": "anomaly_id", "Value": str(anomaly.id)}
                        ]
                        send_template_sms(profile.mobile, template_id, parameters)
                    except UserProfile.DoesNotExist:
                        logger.warning(f"پروفایل برای کاربر {user.username} یافت نشد.")

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success',
                        'message': 'آنومالی با موفقیت ثبت شد',
                        'redirect': reverse('anomalis:anomalis')
                    })
                messages.success(request, 'آنومالی با موفقیت ثبت شد')
                return redirect('anomalis:anomalis')

            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'error',
                        'message': f'خطا در ثبت آنومالی: {str(e)}',
                        'errors': {}
                    })
                messages.error(request, f'خطا در ثبت آنومالی: {str(e)}')
    else:
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
        user_profile = UserProfile.objects.get(user=request.user)
        anomalies = Anomaly.objects.filter(followup=user_profile)
    else:
        anomalies = Anomaly.objects.all()

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
    ws.append(['کد آنومالی', 'مسئول پیگیری', 'ایجاد کننده', 'تاریخ', 'محل', 'شرح', 'اولویت', 'وضعیت'])

    # اضافه کردن داده‌ها
    for anomaly in anomalies:
        jalali_date = to_jalali(anomaly.created_at)

        ws.append([
            anomaly.id,
            f"{anomaly.followup.user.first_name} {anomaly.followup.user.last_name}",
            f"{anomaly.created_by.user.first_name} {anomaly.created_by.user.last_name}",
            jalali_date,
            anomaly.location.name,
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

        # ارسال پیامک به مدیران HSE
        hse_managers = User.objects.filter(groups__name__in=['مدیر HSE', 'افسر HSE'])
        template_id = 254988  # شناسه قالب برای درخواست ایمنی
        for manager in hse_managers:
            try:
                profile = UserProfile.objects.get(user=manager)
                parameters = [
                    {"Name": "status", "Value": "در انتظار تایید"},
                    {"Name": "anomaly_id", "Value": str(anomaly.id)}
                ]
                send_template_sms(profile.mobile, template_id, parameters)
            except UserProfile.DoesNotExist:
                logger.warning(f"پروفایل برای کاربر {manager.username} یافت نشد.")

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
        recipients = [anomaly.created_by, anomaly.followup]
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
        recipients = [anomaly.created_by, anomaly.followup]
        template_id = 320925  # شناسه قالب رد ایمنی
        for recipient in recipients:
            parameters = [
                {"Name": "status", "Value": "رد شده"},
                {"Name": "anomaly_id", "Value": str(anomaly.id)}
            ]
            send_template_sms(recipient.mobile, template_id, parameters)

        return redirect('anomalis:anomaly_detail', pk=anomaly.pk)
