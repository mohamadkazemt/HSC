from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.template.defaultfilters import title
from django.urls import reverse

from accounts.models import UserProfile
from dashboard.models import Notification
from dashboard.sms_utils import send_sms
from .forms import AnomalyForm, CommentForm
from django.shortcuts import redirect
from django.http import JsonResponse
from .models import AnomalyDescription, CorrectiveAction, Comment
from .models import Anomaly
from django.views.decorators.csrf import csrf_exempt
import jdatetime
from accounts.models import UserProfile
from django.contrib.auth.models import Group, User


name = 'anomalis'

@login_required
def anomalis(request):
    if request.method == 'POST':
        form = AnomalyForm(request.POST, request.FILES)
        if form.is_valid():
            anomaly = form.save(commit=False)  # فرم را ذخیره نمی‌کنیم تا بتوانیم فیلد ایجاد کننده را تنظیم کنیم

            try:
                user_profile = UserProfile.objects.get(user=request.user)
            except UserProfile.DoesNotExist:
                return redirect('accounts:login')


            anomaly.created_by = user_profile  # کاربر لاگین شده را به عنوان ایجادکننده تنظیم می‌کنیم  # کاربر لاگین شده را به عنوان ایجادکننده تنظیم می‌کنیم
            anomaly.group = request.user.userprofile.group
            anomaly.hse_type = anomaly.anomalydescription.hse_type  # تنظیم خودکار hse_type از anomalydescription
            anomaly.save()  # حالا فرم را ذخیره می‌کنیم
            return redirect('anomalis:anomalis')
        else:
            print(form.errors)
    else:
        form = AnomalyForm()


    return render(request, 'anomalis/new-anomalie.html', {'form': form,
                                                          'pagetitle':'افزودن آنومالی جدید',
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
    if request.user.groups.filter(name='مسئول پیگیری').exists():
        user_profile = UserProfile.objects.get(user=request.user)
        anomalies = Anomaly.objects.filter(followup=user_profile)
    else:
        anomalies = Anomaly.objects.all()

    # Convert the date fields to Jalali
    for anomaly in anomalies:
        anomaly.created_at_jalali = jdatetime.datetime.fromgregorian(datetime=anomaly.created_at)
        anomaly.updated_at_jalali = jdatetime.datetime.fromgregorian(datetime=anomaly.updated_at)

    paginator = Paginator(anomalies, 10)  # 10 anomalies per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'anomalis/list.html', {
        'page_obj': page_obj,
        'anomalies': anomalies,
        'pagetitle': 'لیست آنومالی‌ها',
        'title': 'لیست آنومالی‌ها'
    })





@login_required
def anomaly_detail_view(request, pk):
    anomaly = get_object_or_404(Anomaly, pk=pk)
    comments = anomaly.comments.filter(parent__isnull=True)

    # بررسی اینکه کاربر عضو گروه 'مدیر HSE' یا 'افسر HSE' است یا خیر
    is_hse_manager = request.user.groups.filter(name__in=['مدیر HSE', 'افسر HSE']).exists()

    # بررسی اینکه آیا درخواست ایمن‌سازی ارسال شده است یا خیر
    is_request_sent = anomaly.is_request_sent  # بررسی از فیلد is_request_sent

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.anomaly = anomaly
            comment.user = request.user
            parent_id = request.POST.get('parent_id')
            if parent_id:
                parent_comment = Comment.objects.get(id=parent_id)
                comment.parent = parent_comment
            comment.save()
            return redirect('anomalis:anomaly_detail', pk=anomaly.id)
    else:
        form = CommentForm()

    context = {
        'anomaly': anomaly,
        'comments': comments,
        'form': form,
        'title': 'جزئیات آنومالی',
        'is_hse_manager': is_hse_manager,
        'is_request_sent': is_request_sent
    }
    return render(request, 'anomalis/anomaly-details.html', context)




@login_required
def request_safe(request, pk):
    anomaly = get_object_or_404(Anomaly, pk=pk)

    if request.method == 'POST' and request.user == anomaly.followup.user:
        # تغییر وضعیت آنومالی به حالت در انتظار تأیید
        anomaly.action = False
        anomaly.is_request_sent = True  # ثبت اینکه درخواست ارسال شده است
        anomaly.save()

        # پیدا کردن مدیران HSE و افسران HSE و ارسال پیامک به شماره موبایل آنها
        hse_managers = User.objects.filter(groups__name__in=['مدیر HSE', 'افسر HSE'])
        for manager in hse_managers:
            try:
                # دریافت شماره موبایل از پروفایل کاربر
                manager_profile = UserProfile.objects.get(user=manager)
                mobile_number = manager_profile.mobile

                # ارسال پیامک
                send_sms(mobile_number, f"درخواست ایمن شدن آنومالی با شماره {anomaly.pk} در انتظار تأیید است.")

                # اضافه کردن نوتیفیکیشن برای هر مدیر HSE و افسر HSE
                Notification.objects.create(
                    user=manager,
                    message=f"درخواست ایمن شدن آنومالی با شماره {anomaly.pk} ارسال شده است.",
                    url=reverse('anomalis:anomaly_detail', args=[anomaly.pk])
                )
            except UserProfile.DoesNotExist:
                print(f"پروفایل برای کاربر {manager.username} وجود ندارد.")

        return redirect('anomalis:anomaly_detail', pk=anomaly.pk)

    return redirect('anomalis:anomalis')





@login_required
@user_passes_test(lambda u: u.groups.filter(name__in=['مدیر HSE', 'افسر HSE']).exists())
def approve_safe(request, pk):
    anomaly = get_object_or_404(Anomaly, pk=pk)

    if request.method == 'POST':
        anomaly.action = True  # تنظیم به حالت ایمن
        anomaly.is_request_sent = False  # درخواست تایید شده و دیگر در انتظار نیست
        anomaly.save()

        # دریافت پروفایل ایجادکننده و مسئول پیگیری
        creator_profile = anomaly.created_by
        followup_profile = anomaly.followup

        # ارسال پیامک به ایجادکننده و مسئول پیگیری
        send_sms(creator_profile.mobile, f"آنومالی با شماره {anomaly.pk} ایمن اعلام شد.")
        send_sms(followup_profile.mobile, f"آنومالی با شماره {anomaly.pk} ایمن اعلام شد.")

        # اضافه کردن نوتیفیکیشن برای ایجادکننده و مسئول پیگیری
        Notification.objects.create(
            user=creator_profile.user,
            message=f"آنومالی با شماره {anomaly.pk} ایمن اعلام شد.",
            url=reverse('anomalis:anomaly_detail', args=[anomaly.pk])
        )
        Notification.objects.create(
            user=followup_profile.user,
            message=f"آنومالی با شماره {anomaly.pk} ایمن اعلام شد.",
            url=reverse('anomalis:anomaly_detail', args=[anomaly.pk])
        )

        return redirect('anomalis:anomaly_detail', pk=anomaly.pk)







@login_required
@user_passes_test(lambda u: u.groups.filter(name__in=['مدیر HSE', 'افسر HSE']).exists())
def reject_safe(request, pk):
    anomaly = get_object_or_404(Anomaly, pk=pk)

    if request.method == 'POST':
        # وضعیت آنومالی تغییر نمی‌کند چون درخواست رد شده است
        anomaly.is_request_sent = False  # ثبت اینکه درخواست لغو شده است
        anomaly.save()

        # دریافت پروفایل ایجادکننده و مسئول پیگیری
        creator_profile = anomaly.created_by
        followup_profile = anomaly.followup

        # ارسال پیامک به ایجادکننده و مسئول پیگیری
        send_sms(creator_profile.mobile, f"درخواست ایمن شدن آنومالی با شماره {anomaly.pk} رد شد.")
        send_sms(followup_profile.mobile, f"درخواست ایمن شدن آنومالی با شماره {anomaly.pk} رد شد.")

        # اضافه کردن نوتیفیکیشن برای ایجادکننده و مسئول پیگیری
        Notification.objects.create(
            user=creator_profile.user,
            message=f"درخواست ایمن شدن آنومالی با شماره {anomaly.pk} رد شد.",
            url=reverse('anomalis:anomaly_detail', args=[anomaly.pk])
        )
        Notification.objects.create(
            user=followup_profile.user,
            message=f"درخواست ایمن شدن آنومالی با شماره {anomaly.pk} رد شد.",
            url=reverse('anomalis:anomaly_detail', args=[anomaly.pk])
        )

        return redirect('anomalis:anomaly_detail', pk=anomaly.pk)

