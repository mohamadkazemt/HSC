from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import ReportForm
from django.contrib.auth.decorators import login_required


@login_required
def create_report(request):
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.user = request.user
            report.save()
            messages.success(request, 'گزارش با موفقیت ثبت شد.')
            return redirect('contractor_management:create_report')
        else:
            messages.error(request, 'خطا در ثبت گزارش. لطفاً خطا ها رو برطرف کنید.')
            errors = form.errors
    else:
        form = ReportForm()
        errors = None

    return render(request, 'contractor_management/create_report.html', {
        'form': form,
        'errors': errors,
        'messages': messages.get_messages(request)
    })




