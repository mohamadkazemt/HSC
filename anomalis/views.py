from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import  AnomalyForm
from django.shortcuts import redirect

from .models import Anomaly

name = 'anomalis'

@login_required
def anomalis(request):
    if request.method == 'POST':
        form = AnomalyForm(request.POST, request.FILES)
        if form.is_valid():
            anomaly = form.save(commit=False)  # فرم را ذخیره نمی‌کنیم تا بتوانیم فیلد ایجاد کننده را تنظیم کنیم
            anomaly.created_by = request.user  # کاربر لاگین شده را به عنوان ایجادکننده تنظیم می‌کنیم
            anomaly.save()  # حالا فرم را ذخیره می‌کنیم
            return redirect('anomalis:anomalis')
        else:
            print(form.errors)
    else:
        form = AnomalyForm()
    return render(request, 'anomalis/new-anomalie.html', {'form': form, 'pagetitle': 'افزودن آنومالی جدید'})



@login_required
#@user_passes_test(lambda u: not u.groups.filter(name='مسئول پیگیری').exists(), login_url='accounts:login')
def anomaly_list(request):
    # بررسی می‌کنیم که آیا کاربر عضو گروه "مسئول پیگیری" هست یا نه
    if request.user.groups.filter(name='مسئول پیگیری').exists():
        # تمام آنومالی‌هایی که کاربر پیگیری آنها است را بازیابی می‌کنیم
        anomalies = Anomaly.objects.filter(followup=request.user)
    else:
        anomalies = Anomaly.objects.all()

    paginator = Paginator(anomalies, 10)  # 10 آنومالی در هر صفحه
    page_number = request.GET.get('page')  # دریافت شماره صفحه از url
    page_obj = paginator.get_page(page_number)

    return render(request, 'anomalis/list.html',{'page_obj': page_obj, 'anomalies': anomalies, 'pagetitle': 'لیست آنومالی‌ها'})
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
def delete_anomaly(request, pk):
    anomaly = get_object_or_404(Anomaly, pk=pk)
    anomaly.delete()
    return redirect('anomalis:anomalis')
