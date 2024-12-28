from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import ReportForm, ReportFilterForm
from django.contrib.auth.decorators import login_required
from .models import Report
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


@login_required
def create_report(request):
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
          report = form.save(commit=False)
          report.user = request.user  # اختصاص کاربر به گزارش
          report.report_datetime = timezone.now() # اضافه کردن زمان گزارش
          from .utils import get_current_user_shift_and_group
          current_shift, current_group = get_current_user_shift_and_group(report.user)
          if current_shift and current_group:
            report.shift = current_shift
            report.group = current_group
          else:
              messages.error(request, 'امکان ثبت گزارش در این بازه زمانی وجود ندارد.')
              return render(request, 'contractor_management/create_report.html', {
                  'form': form,
                  'messages': messages.get_messages(request)
              })

          if report.report_datetime: # چک کردن برای وجود تاریخ
              existing_report = Report.objects.filter(
                vehicle = report.vehicle,
                report_datetime__date=report.report_datetime.date(),
                shift = report.shift
              ).exists()
              if existing_report:
                messages.error(request, 'برای این خودرو در این شیفت و تاریخ یک گزارش ثبت شده است.')
                return render(request, 'contractor_management/create_report.html', {
                    'form': form,
                    'messages': messages.get_messages(request)
                })
              else:
                  report.save()
                  messages.success(request, 'گزارش با موفقیت ثبت شد.')
                  return redirect('contractor_management:create_report')

        else:
            messages.error(request, 'خطا در ثبت گزارش. لطفاً خطا ها رو برطرف کنید.')
    else:
        form = ReportForm()

    return render(request, 'contractor_management/create_report.html', {
        'form': form,
        'messages': messages.get_messages(request)
    })



@login_required
def all_reports(request):
    form = ReportFilterForm(request.GET)
    reports = Report.objects.all()
    query = Q()

    if form.is_valid():
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        contractor = form.cleaned_data.get('contractor')
        vehicle = form.cleaned_data.get('vehicle')
        shift = form.cleaned_data.get('shift')
        group = form.cleaned_data.get('group')
        if start_date and end_date:
            query &= Q(report_datetime__date__range=[start_date, end_date])
        elif start_date:
            query &= Q(report_datetime__date__gte=start_date)
        elif end_date:
            query &= Q(report_datetime__date__lte=end_date)
        if contractor:
            query &= Q(contractor__company_name=contractor)
        if vehicle:
            query &= Q(vehicle__license_plate=vehicle)
        if shift:
          query &= Q(shift=shift)
        if group:
            query &= Q(group=group)


    reports = reports.filter(query)
    paginator = Paginator(reports, 10)  # Show 10 reports per page

    page = request.GET.get('page')
    try:
        reports = paginator.page(page)
    except PageNotAnInteger:
        reports = paginator.page(1)
    except EmptyPage:
        reports = paginator.page(paginator.num_pages)
    return render(request, 'contractor_management/reports/all_reports.html', {
        'reports': reports,
        'form': form,
    })