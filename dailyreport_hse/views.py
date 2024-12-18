from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import (
    DailyReport, BlastingDetail, DrillingDetail, DumpDetail,
    LoadingDetail, InspectionDetail, StoppageDetail, FollowupDetail
)
from BaseInfo.models import MiningBlock, MiningMachine, Dump
from .forms import DailyReportForm
import json
import logging
from shift_manager.utils import get_current_shift_and_group
from django.db import IntegrityError
from django.utils.timezone import make_aware
from datetime import datetime

# تنظیم لاگر برای مدیریت خطا و دیباگ
logger = logging.getLogger(__name__)

@login_required
def create_daily_report(request):
    """
    ویوی ایجاد گزارش روزانه برای افسران ایمنی.
    """
    # دریافت شیفت و گروه کاری از اپ shift_manager
    current_shift, current_group = get_current_shift_and_group()
    if not current_shift or not current_group:
        messages.error(request, "مشکلی در تعیین شیفت و گروه کاری وجود دارد. لطفاً با مدیر سیستم تماس بگیرید.")
        return redirect('dashboard')

    # داده‌های داینامیک برای فرم‌ها
    report_form = DailyReportForm()
    mining_blocks = list(MiningBlock.objects.filter(is_active=True).values('id', 'block_name'))
    mining_machines = list(MiningMachine.objects.filter(is_active=True).values('id', 'workshop_code', 'machine_type__name'))
    dumps = list(Dump.objects.filter(is_active=True).values('id', 'dump_name'))

    if request.method == "POST":
        try:
            # فرم اصلی DailyReport
            report_data = request.POST.copy()
            report_data['shift'] = current_shift  # اضافه کردن شیفت محاسبه شده
            report_data['work_group'] = current_group  # اضافه کردن گروه کاری محاسبه شده
            report_form = DailyReportForm(report_data)

            logger.debug("POST data: %s", request.POST)
            logger.debug("FILES data: %s", request.FILES)

            if report_form.is_valid():
                # ذخیره گزارش اصلی
                report = report_form.save(commit=False)
                report.user = request.user  # تنظیم کاربر ایجاد کننده
                report.save()
                logger.info("گزارش اصلی با موفقیت ذخیره شد. ID: %s", report.id)

                # ذخیره جزئیات آتشباری از JSON
                blasting_details_json = request.POST.get('blasting_details')
                if blasting_details_json:
                    try:
                        blasting_details = json.loads(blasting_details_json)
                        for detail in blasting_details:
                            if not MiningBlock.objects.filter(id=detail.get('block_id')).exists():
                                logger.error("Block ID %s does not exist.", detail.get('block_id'))
                                continue
                            BlastingDetail.objects.create(
                                daily_report=report,
                                block_id=detail.get('block_id'),
                                description=detail.get('description', '')
                            )
                        logger.info("جزئیات آتشباری ذخیره شد.")
                    except json.JSONDecodeError as e:
                        logger.error("خطا در پردازش JSON آتشباری: %s", e)

                # ذخیره جزئیات حفاری از JSON
                drilling_details_json = request.POST.get('drilling_details')
                if drilling_details_json:
                    try:
                        drilling_details = json.loads(drilling_details_json)
                        for detail in drilling_details:
                            if not MiningBlock.objects.filter(id=detail.get('block_id')).exists():
                                logger.error("Block ID %s does not exist.", detail.get('block_id'))
                                continue
                            if not MiningMachine.objects.filter(id=detail.get('machine_id')).exists():
                                logger.error("Machine ID %s does not exist.", detail.get('machine_id'))
                                continue
                            DrillingDetail.objects.create(
                                daily_report=report,
                                block_id=detail.get('block_id'),
                                machine_id=detail.get('machine_id'),
                                status=detail.get('status', 'safe')
                            )
                        logger.info("جزئیات حفاری ذخیره شد.")
                    except json.JSONDecodeError as e:
                        logger.error("خطا در پردازش JSON حفاری: %s", e)

                # ذخیره جزئیات بارگیری از JSON
                loading_details_json = request.POST.get('loading_details')
                if loading_details_json:
                    try:
                        loading_details = json.loads(loading_details_json)
                        for detail in loading_details:
                            if not MiningBlock.objects.filter(id=detail.get('block_id')).exists():
                                logger.error("Block ID %s does not exist.", detail.get('block_id'))
                                continue
                            if not MiningMachine.objects.filter(id=detail.get('machine_id')).exists():
                                logger.error("Machine ID %s does not exist.", detail.get('machine_id'))
                                continue
                            LoadingDetail.objects.create(
                                daily_report=report,
                                block_id=detail.get('block_id'),
                                machine_id=detail.get('machine_id'),
                                status=detail.get('status', 'safe')
                            )
                        logger.info("جزئیات بارگیری ذخیره شد.")
                    except json.JSONDecodeError as e:
                        logger.error("خطا در پردازش JSON بارگیری: %s", e)

                # ذخیره جزئیات تخلیه از JSON
                dump_details_json = request.POST.get('dump_details')
                if dump_details_json:
                    try:
                        dump_details = json.loads(dump_details_json)  # تبدیل JSON به لیست
                        for detail in dump_details:
                            dump_id = detail.get('dump_id')
                            status = detail.get('status', 'safe')
                            description = detail.get('description', '')

                            # بررسی معتبر بودن dump_id
                            if not dump_id or not Dump.objects.filter(id=dump_id).exists():
                                logger.error("Dump ID %s does not exist or is invalid.", dump_id)
                                messages.error(request, f"دامپ با ID {dump_id} وجود ندارد.")
                                continue  # پرش به جزئیات بعدی

                            # ذخیره جزئیات تخلیه
                            DumpDetail.objects.create(
                                daily_report=report,
                                dump_id=dump_id,
                                status=status,
                                description=description
                            )
                            logger.info("جزئیات تخلیه برای دامپ ID %s ذخیره شد.", dump_id)

                    except json.JSONDecodeError as e:
                        logger.error("خطا در پردازش JSON تخلیه: %s", e)
                        messages.error(request, "خطا در پردازش اطلاعات تخلیه. لطفاً مجدداً تلاش کنید.")
                    except Exception as e:
                        logger.exception("خطای غیرمنتظره در ذخیره جزئیات تخلیه: %s", e)
                        messages.error(request, "یک خطای غیرمنتظره رخ داد.")

                # ذخیره جزئیات بازرسی از JSON
                inspection_details_json = request.POST.get('inspection_details')
                if inspection_details_json:
                    try:
                        inspection_details = json.loads(inspection_details_json)
                        for detail in inspection_details:
                            InspectionDetail.objects.create(
                                daily_report=report,
                                inspection_done=detail.get('inspection_done', False),
                                status=detail.get('status', 'safe'),
                                description=detail.get('description', '')
                            )
                        logger.info("جزئیات بازرسی ذخیره شد.")
                    except json.JSONDecodeError as e:
                        logger.error("خطا در پردازش JSON بازرسی: %s", e)

                # ذخیره جزئیات توقفات از JSON
                stoppage_details_json = request.POST.get('stoppage_details')
                if stoppage_details_json:
                    try:
                        stoppage_details = json.loads(stoppage_details_json)
                        for detail in stoppage_details:
                            start_time = make_aware(datetime.strptime(detail.get('start_time'), "%H:%M"))
                            end_time = make_aware(datetime.strptime(detail.get('end_time'), "%H:%M"))
                            StoppageDetail.objects.create(
                                daily_report=report,
                                reason=detail.get('reason'),
                                start_time=start_time,
                                end_time=end_time,
                                description=detail.get('description', '')
                            )
                        logger.info("جزئیات توقفات ذخیره شد.")
                    except json.JSONDecodeError as e:
                        logger.error("خطا در پردازش JSON توقفات: %s", e)

                # ذخیره جزئیات پیگیری از JSON
                followup_details_json = request.POST.get('followup_details')
                if followup_details_json:
                    try:
                        followup_details = json.loads(followup_details_json)
                        for detail in followup_details:
                            FollowupDetail.objects.create(
                                daily_report=report,
                                description=detail.get('description', ''),
                                files=request.FILES.get(detail.get('file_input_name'))
                            )
                        logger.info("جزئیات پیگیری ذخیره شد.")
                    except json.JSONDecodeError as e:
                        logger.error("خطا در پردازش JSON پیگیری: %s", e)

                messages.success(request, "گزارش روزانه با موفقیت ثبت شد!")
                return redirect('dailyreport_hse:report_list')
            else:
                logger.warning("فرم DailyReport نامعتبر است: %s", report_form.errors)
                messages.error(request, "خطا در ثبت فرم. لطفاً مقادیر را به درستی وارد کنید.")

        except IntegrityError as e:
            logger.exception("خطای مربوط به محدودیت FOREIGN KEY: %s", e)
            messages.error(request, "خطا در ذخیره داده‌ها به دلیل مشکلات کلید خارجی. لطفاً بررسی کنید که همه مقادیر صحیح هستند.")
        except Exception as e:
            logger.exception("خطای غیرمنتظره در پردازش فرم: %s", e)
            messages.error(request, "یک خطای غیرمنتظره رخ داد. لطفاً با مدیر سیستم تماس بگیرید.")

    return render(request, 'dailyreport_hse/create_shift_report.html', {
        'report_form': report_form,
        'mining_blocks': mining_blocks,
        'mining_machines': mining_machines,
        'dumps': dumps,
    })

