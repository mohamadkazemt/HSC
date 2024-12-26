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
            return redirect('report_success')
    else:
        form = ReportForm()
    return render(request, 'contractor_management/create_report.html', {'form': form})


@login_required
def report_success(request):
    return render(request, 'contractor_management/report_success.html')


from django.shortcuts import render

# Create your views here.
