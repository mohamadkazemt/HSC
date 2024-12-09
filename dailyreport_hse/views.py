import os
import json
from django.apps import apps
from django.shortcuts import render, redirect
from django.http import Http404, JsonResponse
from dailyreport_hse.models import (
    BlastingOperation,
    DrillingOperation,
    LoadingOperation,
    WorkshopInspection,
    SafetyIssue,
    ShiftFollowUp,
    ShiftReport
)
from BaseInfo.models import MiningBlock, MiningMachine, Dump  # اضافه کردن مدل‌های مرتبط


def create_shift_report(request):
    # خواندن فایل JSON
    steps_file_path = os.path.join(apps.get_app_config('dailyreport_hse').path, 'steps.json')
    if not os.path.exists(steps_file_path):
        raise Http404("فایل steps.json یافت نشد.")

    with open(steps_file_path, 'r', encoding='utf-8') as file:
        steps = json.load(file)

    # فراخوانی داده‌های پویا
    blocks = MiningBlock.objects.all()
    machines = MiningMachine.objects.all()
    dumps = Dump.objects.all()

    if request.method == 'POST':
        # پردازش فرم‌ها
        try:
            shift_date = request.POST.get('shift_date')
            shift_time = request.POST.get('shift_time')
            shift_report = ShiftReport.objects.create(
                shift_date=shift_date,
                shift_time=shift_time
            )

            # عملیات آتش‌باری
            blasting_done = request.POST.get('blasting_done') == 'yes'
            block_id = request.POST.get('blasting_block')
            if block_id:
                BlastingOperation.objects.create(
                    shift_report=shift_report,
                    blasting_done=blasting_done,
                    block_id=block_id
                )

            # عملیات حفاری
            drilling_site = request.POST.get('drilling_site')
            drilling_machine = request.POST.get('drilling_machine')
            if drilling_site and drilling_machine:
                DrillingOperation.objects.create(
                    shift_report=shift_report,
                    site_id=drilling_site,
                    machine_id=drilling_machine,
                    approved=request.POST.get('drilling_approved') == 'yes',
                    comments=request.POST.get('drilling_comments', '')
                )

            # عملیات بارگیری
            workface = request.POST.get('loading_workface')
            dump = request.POST.get('loading_dump')
            if workface and dump:
                LoadingOperation.objects.create(
                    shift_report=shift_report,
                    workface_id=workface,
                    dump_id=dump,
                    approved=request.POST.get('loading_approved') == 'yes',
                    comments=request.POST.get('loading_comments', '')
                )

            # بازدید تعمیرگاه
            inspection_done = request.POST.get('inspection_done') == 'yes'
            WorkshopInspection.objects.create(
                shift_report=shift_report,
                inspection_done=inspection_done,
                approved=request.POST.get('inspection_approved') == 'yes',
                comments=request.POST.get('inspection_comments', '')
            )

            # مشکلات ایمنی
            safety_issues = request.POST.getlist('safety_issues')
            for issue in safety_issues:
                SafetyIssue.objects.create(
                    shift_report=shift_report,
                    issue_description=issue
                )

            # پیگیری شیفت بعد
            follow_up_description = request.POST.get('follow_up')
            if follow_up_description:
                ShiftFollowUp.objects.create(
                    shift_report=shift_report,
                    follow_up_description=follow_up_description
                )

            return JsonResponse({'status': 'success', 'message': 'گزارش با موفقیت ذخیره شد!'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    # ارسال داده‌ها به قالب
    return render(request, 'dailyreport_hse/new-report.html', {
        'steps': steps,
        'blocks': blocks,
        'machines': machines,
        'dumps': dumps
    })
