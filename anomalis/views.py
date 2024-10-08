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
@user_passes_test(lambda u: not u.groups.filter(name='مسئول پیگیری').exists(), login_url='accounts:login')
def anomaly_list(request):
    anomalies = Anomaly.objects.all()  # گرفتن همه آنومالی‌ها از مدل
    return render(request, 'anomalis/list.html',{'anomalies': anomalies, 'pagetitle': 'لیست آنومالی‌ها'})
@login_required
def toggle_status(request, pk):
    anomaly = get_object_or_404(Anomaly, pk=pk)
    anomaly.action = not anomaly.action  # تغییر وضعیت
    anomaly.save()
    return redirect('anomalis:anomalis')  # بازگشت به لیست آنومالی‌ه

@login_required

def edit_anomaly(request, pk):
    anomaly = get_object_or_404(Anomaly, pk=pk)
    if request.method == 'POST':
        form = AnomalyForm(request.POST, instance=anomaly)
        if form.is_valid():
            form.save()
            return redirect('anomalis:anomalis')
    else:
        form = AnomalyForm(instance=anomaly)
    return render(request, 'anomalis/list.html', {'form': form})

@login_required
def delete_anomaly(request, pk):
    anomaly = get_object_or_404(Anomaly, pk=pk)
    anomaly.delete()
    return redirect('anomalis:anomalis')
