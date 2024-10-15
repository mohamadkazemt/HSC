from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.template.defaultfilters import title
from accounts.models import UserProfile
from .forms import AnomalyForm, CommentForm
from django.shortcuts import redirect
from django.http import JsonResponse
from .models import AnomalyDescription, CorrectiveAction, Comment
from .models import Anomaly
from django.views.decorators.csrf import csrf_exempt
import jdatetime





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
        anomalies = Anomaly.objects.filter(followup=request.user)
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
def toggle_status(request, pk):
    anomaly = get_object_or_404(Anomaly, pk=pk)
    anomaly.action = not anomaly.action  # تغییر وضعیت
    anomaly.save()
    return redirect('anomalis:anomalis')  # بازگشت به لیست آنومالی‌ه

@login_required
def edit_anomaly(request, pk):
    anomaly = get_object_or_404(Anomaly, pk=pk)  # گرفتن آنومالی مورد نظر از دیتابیس

    if request.method == 'POST':
        form = AnomalyForm(request.POST, request.FILES, instance=anomaly)  # استفاده از اینستنس برای ویرایش
        if form.is_valid():
            form.save()  # ذخیره تغییرات
            return redirect('anomalis:anomalis')  # بازگشت به صفحه لیست یا هر صفحه دیگری
    else:
        form = AnomalyForm(instance=anomaly)  # نمایش اطلاعات موجود در فرم

    return render(request, 'anomalis/edit_anomaly.html', {'form': form})







@login_required
def anomaly_detail_view(request, pk):
    anomaly = get_object_or_404(Anomaly, pk=pk)
    comments = anomaly.comments.filter(parent__isnull=True)  # فقط کامنت‌های سطح بالا

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.anomaly = anomaly
            # پیدا کردن پروفایل کاربر و انتساب آن به کامنت
            comment.user = UserProfile.objects.get(user=request.user)  # به جای request.user، پروفایل کاربر را واکشی می‌کنیم
            parent_id = request.POST.get('parent_id')  # بررسی اینکه آیا این کامنت، پاسخ به یک کامنت دیگر است
            if parent_id:
                parent_comment = Comment.objects.get(id=parent_id)
                comment.parent = parent_comment  # تنظیم والد برای کامنت
            comment.save()
            return redirect('anomalis:anomaly_detail', pk=anomaly.id)
    else:
        form = CommentForm()

    context = {
        'anomaly': anomaly,
        'comments': comments,
        'form': form,  # ارسال فرم به قالب
    }
    return render(request, 'anomalis/anomaly-details.html', context)

