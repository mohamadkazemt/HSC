from django.shortcuts import render, redirect
from django.contrib import messages
from .models import (
    DailyReport, BlastingDetail, DrillingDetail, DumpDetail,
    LoadingDetail, InspectionDetail, StoppageDetail, FollowupDetail
)
from BaseInfo.models import MiningBlock, MiningMachine, Dump
from .forms import DailyReportForm
from django.forms import modelformset_factory


def create_daily_report(request):
    """
    ویوی ایجاد گزارش روزانه برای افسران ایمنی.
    """
    if request.method == "POST":
        # فرم اصلی DailyReport
        report_form = DailyReportForm(request.POST)

        if report_form.is_valid():
            # ذخیره گزارش اصلی
            report = report_form.save(commit=False)
            report.user = request.user  # تنظیم کاربر ایجاد کننده
            report.save()

            # ذخیره جزئیات آتشباری
            for i in range(int(request.POST.get('blasting_count', 0))):
                if request.POST.get(f'blasting_block_{i}'):
                    BlastingDetail.objects.create(
                        daily_report=report,
                        block_id=request.POST.get(f'blasting_block_{i}'),
                        description=request.POST.get(f'blasting_description_{i}', '')
                    )

            # ذخیره جزئیات حفاری
            for i in range(int(request.POST.get('drilling_count', 0))):
                if request.POST.get(f'drilling_block_{i}') and request.POST.get(f'drilling_machine_{i}'):
                    DrillingDetail.objects.create(
                        daily_report=report,
                        block_id=request.POST.get(f'drilling_block_{i}'),
                        machine_id=request.POST.get(f'drilling_machine_{i}'),
                        status=request.POST.get(f'drilling_status_{i}', 'safe')
                    )

            # ذخیره جزئیات تخلیه
            for i in range(int(request.POST.get('dump_count', 0))):
                if request.POST.get(f'dump_{i}'):
                    DumpDetail.objects.create(
                        daily_report=report,
                        dump_id=request.POST.get(f'dump_{i}'),
                        status=request.POST.get(f'dump_status_{i}', 'safe'),
                        description=request.POST.get(f'dump_description_{i}', '')
                    )

            # ذخیره جزئیات بارگیری
            for i in range(int(request.POST.get('loading_count', 0))):
                if request.POST.get(f'loading_block_{i}') and request.POST.get(f'loading_machine_{i}'):
                    LoadingDetail.objects.create(
                        daily_report=report,
                        block_id=request.POST.get(f'loading_block_{i}'),
                        machine_id=request.POST.get(f'loading_machine_{i}'),
                        status=request.POST.get(f'loading_status_{i}', 'safe')
                    )

            # ذخیره جزئیات بازرسی
            if request.POST.get('inspection_status') == 'yes':
                InspectionDetail.objects.create(
                    daily_report=report,
                    inspection_done=True,
                    status=request.POST.get('inspection_status_detail', 'safe'),
                    description=request.POST.get('inspection_description', '')
                )

            # ذخیره جزئیات توقفات
            for i in range(int(request.POST.get('stoppage_count', 0))):
                if request.POST.get(f'stoppage_reason_{i}') and request.POST.get(
                        f'stoppage_start_{i}') and request.POST.get(f'stoppage_end_{i}'):
                    StoppageDetail.objects.create(
                        daily_report=report,
                        reason=request.POST.get(f'stoppage_reason_{i}'),
                        start_time=request.POST.get(f'stoppage_start_{i}'),
                        end_time=request.POST.get(f'stoppage_end_{i}'),
                        description=request.POST.get(f'stoppage_description_{i}', '')
                    )

            # ذخیره جزئیات پیگیری
            for i in range(int(request.POST.get('followup_count', 0))):
                FollowupDetail.objects.create(
                    daily_report=report,
                    description=request.POST.get(f'followup_description_{i}', ''),
                    files=request.FILES.get(f'followup_files_{i}')
                )

            messages.success(request, "گزارش روزانه با موفقیت ثبت شد!")
            return redirect('dailyreport_hse:report_list')

    else:
        # داده‌های داینامیک برای فرم‌ها
        report_form = DailyReportForm()
        mining_blocks = MiningBlock.objects.all()
        mining_machines = MiningMachine.objects.all()
        dumps = Dump.objects.all()
        print(mining_blocks)
        print(mining_machines)
        print(dumps)


    return render(request, 'dailyreport_hse/create_shift_report.html', {
        'report_form': report_form,
        'mining_blocks': mining_blocks,
        'mining_machines': mining_machines,
        'dumps': dumps,
    })
