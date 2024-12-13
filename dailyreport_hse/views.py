from django.shortcuts import render, redirect
from .forms import (
    DailyReportForm,
    BlastingDetailFormset,
    DrillingDetailFormset,
    DumpDetailFormset,
    LoadingDetailFormset,
    InspectionDetailForm,
    StoppageDetailForm,
    FollowupDetailForm,
)
from .models import DailyReport, BlastingDetail, DrillingDetail, DumpDetail, LoadingDetail, InspectionDetail, StoppageDetail, FollowupDetail


def create_daily_report(request):
    """
    مدیریت مراحل گزارش روزانه:
    1. آتشباری
    2. حفاری
    3. دامپ‌ها
    4. بارگیری
    5. تعمیرگاه
    6. توقفات
    7. پیگیری
    """
    if request.method == "POST":
        # فرم اصلی گزارش
        report_form = DailyReportForm(request.POST)

        # فرمست‌ها و فرم‌های مراحل
        blasting_formset = BlastingDetailFormset(request.POST, queryset=BlastingDetail.objects.none(), prefix="blasting")
        drilling_formset = DrillingDetailFormset(request.POST, queryset=DrillingDetail.objects.none(), prefix="drilling")
        dump_formset = DumpDetailFormset(request.POST, queryset=DumpDetail.objects.none(), prefix="dump")
        loading_formset = LoadingDetailFormset(request.POST, queryset=LoadingDetail.objects.none(), prefix="loading")
        inspection_form = InspectionDetailForm(request.POST, prefix="inspection")
        stoppage_form = StoppageDetailForm(request.POST, prefix="stoppage")
        followup_form = FollowupDetailForm(request.POST, request.FILES, prefix="followup")

        # بررسی اعتبار فرم‌ها
        if report_form.is_valid() and all([
            blasting_formset.is_valid(),
            drilling_formset.is_valid(),
            dump_formset.is_valid(),
            loading_formset.is_valid(),
            inspection_form.is_valid(),
            stoppage_form.is_valid(),
            followup_form.is_valid(),
        ]):
            # ذخیره گزارش اصلی
            report = report_form.save(commit=False)
            report.user = request.user  # اتصال گزارش به کاربر فعلی
            report.save()

            # ذخیره فرمست‌ها
            def save_details(formset, report_instance):
                instances = formset.save(commit=False)
                for instance in instances:
                    instance.daily_report = report_instance
                    instance.save()

            save_details(blasting_formset, report)
            save_details(drilling_formset, report)
            save_details(dump_formset, report)
            save_details(loading_formset, report)

            # ذخیره مراحل دیگر
            inspection = inspection_form.save(commit=False)
            inspection.daily_report = report
            inspection.save()

            stoppage = stoppage_form.save(commit=False)
            stoppage.daily_report = report
            stoppage.save()

            followup = followup_form.save(commit=False)
            followup.daily_report = report
            followup.save()

            return redirect('hsec:report_success')  # انتقال به صفحه موفقیت

    else:
        # فرم‌ها برای درخواست GET
        report_form = DailyReportForm()
        blasting_formset = BlastingDetailFormset(queryset=BlastingDetail.objects.none(), prefix="blasting")
        drilling_formset = DrillingDetailFormset(queryset=DrillingDetail.objects.none(), prefix="drilling")
        dump_formset = DumpDetailFormset(queryset=DumpDetail.objects.none(), prefix="dump")
        loading_formset = LoadingDetailFormset(queryset=LoadingDetail.objects.none(), prefix="loading")
        inspection_form = InspectionDetailForm(prefix="inspection")
        stoppage_form = StoppageDetailForm(prefix="stoppage")
        followup_form = FollowupDetailForm(prefix="followup")

    return render(request, 'dailyreport_hse/new-report.html', {
        'report_form': report_form,
        'blasting_formset': blasting_formset,
        'drilling_formset': drilling_formset,
        'dump_formset': dump_formset,
        'loading_formset': loading_formset,
        'inspection_form': inspection_form,
        'stoppage_form': stoppage_form,
        'followup_form': followup_form,
    })


def report_success(request):
    """
    صفحه تأیید موفقیت ارسال گزارش
    """
    return render(request, 'report_success.html', {
        'message': 'گزارش شما با موفقیت ثبت شد.',
    })
