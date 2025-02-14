from django.contrib.auth.decorators import login_required
from django.core.checks import messages
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404, redirect

from accounts.models import UserProfile
from .models import (
    DailyReport, BlastingDetail, DrillingDetail, LoadingDetail, DumpDetail,
    StoppageDetail, FollowupDetail, InspectionDetail
)
from BaseInfo.models import MiningBlock, MiningMachine, Dump
from django.views.generic import TemplateView, DetailView
from django.urls import path
from shift_manager.utils import get_current_shift_and_group
import logging
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.core.files.base import ContentFile
import base64
import json
from django.template.loader import render_to_string
from weasyprint import HTML
from django.http import HttpResponse
from django.conf import settings
import os
from permissions.utils import class_permission_required, permission_required
from django.contrib import messages
import logging
from django.core.exceptions import ValidationError
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
import logging

logger = logging.getLogger(__name__)






class CreateDailyReportView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            print("Incoming Data:", request.data)
            print("Incoming Files:", request.FILES)

            # دریافت داده‌های اصلی
            received_data = request.data
            # تجزیه رشته‌های JSON به لیست های پایتون
            blasting_details = json.loads(received_data.get("blasting_details", "[]"))
            drilling_details = json.loads(received_data.get("drilling_details", "[]"))
            loading_details = json.loads(received_data.get("loading_details", "[]"))
            dump_details = json.loads(received_data.get("dump_details", "[]"))
            stoppage_details = json.loads(received_data.get("stoppage_details", "[]"))
            inspection_details = json.loads(
                received_data.get("inspection_details", "[]")
            )

            # followups_data = received_data.get("followups", []) # دیگه نیازی به این نداریم

            print("Files Received:", request.FILES)
            # دریافت شیفت و گروه کاری جاری
            current_shift, current_group = get_current_shift_and_group(request.user)

            if not current_shift or not current_group:
                return Response(
                    {"error": "شیفت یا گروه کاری جاری شناسایی نشد."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # ساختن گزارش روزانه
            daily_report = DailyReport(
                user=request.user,
                shift=current_shift,
                work_group=current_group,
                supervisor_comments=received_data.get("supervisor_comments", ""),
            )

            # اعتبارسنجی گزارش روزانه
            try:
                daily_report.full_clean()
            except ValidationError as e:
                return Response(
                    {"error": "Validation Error", "errors": e.message_dict},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            daily_report.save()

            # ذخیره جزئیات آتشباری
            for blasting in blasting_details:
                if blasting.get("block_id"):
                    block = get_object_or_404(MiningBlock, id=blasting.get("block_id"))
                    BlastingDetail.objects.create(
                        daily_report=daily_report,
                        explosion_occurred=blasting.get("explosion_occurred", False),
                        block=block,
                        description=blasting.get("description", ""),
                    )

            # ذخیره جزئیات حفاری
            for drilling in drilling_details:
                if drilling.get("block_id") and drilling.get("machine_id"):
                    block = get_object_or_404(MiningBlock, id=drilling.get("block_id"))
                    machine = get_object_or_404(
                        MiningMachine, id=drilling.get("machine_id")
                    )
                    DrillingDetail.objects.create(
                        daily_report=daily_report,
                        block=block,
                        machine=machine,
                        status=drilling.get("status", "unknown"),
                        description=drilling.get("description", ""),
                    )

            # ذخیره جزئیات بارگیری
            for loading in loading_details:
                if loading.get("block_id") and loading.get("machine_id"):
                    block = get_object_or_404(MiningBlock, id=loading.get("block_id"))
                    machine = get_object_or_404(
                        MiningMachine, id=loading.get("machine_id")
                    )
                    LoadingDetail.objects.create(
                        daily_report=daily_report,
                        block=block,
                        machine=machine,
                        status=loading.get("status", "unknown"),
                        description=loading.get("description", ""),
                    )

            # ذخیره جزئیات تخلیه
            for dump_detail in dump_details:
                if dump_detail.get("dump_id"):
                    dump = get_object_or_404(Dump, id=dump_detail.get("dump_id"))
                    DumpDetail.objects.create(
                        daily_report=daily_report,
                        dump=dump,
                        status=dump_detail.get("status", "unknown"),
                        description=dump_detail.get("description", ""),
                    )

            # ذخیره جزئیات توقف
            for stoppage in stoppage_details:  # Iterate through stoppage details
                StoppageDetail.objects.create(
                    daily_report=daily_report,
                    reason=stoppage.get("reason", ""),
                    start_time=stoppage.get("start_time", None),
                    end_time=stoppage.get("end_time", None),
                )

            # ذخیره جزئیات پیگیری
            # for index, followup in enumerate(followups_data): #دیگه لازم نیست روی followup_data حلقه بزنیم
            index = 0 # فقط یک پیگیری در این مثال داریم، برای توسعه میتونید حلقه بزنید
            description = received_data.get(f"followups[{index}][followup_description]")
            files = request.FILES.getlist(f"followups[{index}][followup_file]")

            followup_instance = FollowupDetail.objects.create(
                daily_report=daily_report, description=description
            )

            # بررسی و ذخیره فایل‌ها
            for file in files:
                followup_instance.files.save(file.name, file)


            # ذخیره جزئیات بازرسی
            for inspection in inspection_details:
                InspectionDetail.objects.create(
                    daily_report=daily_report,
                    inspection_done=inspection.get("inspection_done", False),
                    inspection=inspection.get("inspection", ""),  # فیلد inspection رو اضافه کنید
                    status=inspection.get("status", "unknown"),
                    description=inspection.get("description", ""),
                )

            return Response(
                {"message": "گزارش با موفقیت ثبت شد.", "id": daily_report.id},
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            print(f"خطا: {e}")
            return Response(
                {"error": str(e), "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )





@class_permission_required("daily_report_form")
class DailyReportFormView(LoginRequiredMixin, TemplateView):
    template_name = "dailyreport_hse/create_shift_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mining_blocks'] = MiningBlock.objects.all()

        # فیلتر کردن MiningMachine ها بر اساس اسم گروه کاری
        drilling_machines = MiningMachine.objects.filter(machine_type__machine_workgroup__name="حفاری")
        loading_machines = MiningMachine.objects.filter(machine_type__machine_workgroup__name="بارکننده")

        # لاگ کوئری ها
        logger.info(f"Drilling Machines Query: {drilling_machines.query}")
        logger.info(f"Loading Machines Query: {loading_machines.query}")

        # لاگ تعداد نتایج
        logger.info(f"Number of Drilling Machines: {drilling_machines.count()}")
        logger.info(f"Number of Loading Machines: {loading_machines.count()}")

        context['drilling_machines'] = drilling_machines
        context['loading_machines'] = loading_machines
        context['dumps'] = Dump.objects.all()
        return context





@class_permission_required("daily_report_list")
class DailyReportListView(LoginRequiredMixin, ListView):
    model = DailyReport
    template_name = "dailyreport_hse/daily_report_list.html"
    context_object_name = "daily_reports"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()

        # دریافت پارامترهای فیلتر
        shift = self.request.GET.get("shift")
        group = self.request.GET.get("group")
        search_query = self.request.GET.get("search")

        # اعمال فیلترها (فقط اگر مقداری برای فیلتر وارد شده باشد)
        if shift and shift != "همه":
            queryset = queryset.filter(shift=shift)
        if group and group != "همه":
            queryset = queryset.filter(work_group=group)

        # اعمال فیلتر جستجو (بهبود یافته)
        if search_query:
            queryset = queryset.filter(
                Q(user__username__icontains=search_query) |
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(user__userprofile__personnel_code__icontains=search_query) |
                Q(supervisor_comments__icontains=search_query) |
                Q(shift__icontains=search_query)
                # میتونید فیلد های دیگه ای رو هم اینجا اضافه کنید
            )

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # ارسال فیلترهای فعلی به تمپلیت برای نمایش انتخاب‌ها
        context["shift_filter"] = self.request.GET.get("shift", "همه")
        context["group_filter"] = self.request.GET.get("group", "همه")
        context["search_query"] = self.request.GET.get("search", "")
        return context

@class_permission_required("daily_report_detail")

class DailyReportDetailView(LoginRequiredMixin, DetailView):
    model = DailyReport
    template_name = "dailyreport_hse/daily_report_detail.html"
    context_object_name = "report"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # گزارش اصلی
        report = self.object

        # اضافه کردن جزئیات مرتبط به کانتکست
        context['blasting_details'] = BlastingDetail.objects.filter(daily_report=report)
        context['drilling_details'] = DrillingDetail.objects.filter(daily_report=report)
        context['loading_details'] = LoadingDetail.objects.filter(daily_report=report)
        context['dump_details'] = DumpDetail.objects.filter(daily_report=report)
        context['stoppage_details'] = StoppageDetail.objects.filter(daily_report=report)
        context['followup_details'] = FollowupDetail.objects.filter(daily_report=report)
        context['inspection_details'] = InspectionDetail.objects.filter(daily_report=report)
        context['title'] = 'گزارش روزانه'

        return context

@permission_required("daily_report_pdf")

@login_required
def daily_report_pdf_view(request, pk):
    # دریافت گزارش روزانه
    daily_report = get_object_or_404(DailyReport, pk=pk)

    # دریافت اطلاعات کاربر و امضا
    user_profile = get_object_or_404(UserProfile, user=daily_report.user)
    user_signature = user_profile.signature.url if user_profile.signature else None

    # دریافت جزئیات پیگیری
    followup_details = []
    for detail in FollowupDetail.objects.filter(daily_report=daily_report):
        followup_details.append({
            'description': detail.description,
            'has_attachment': True if detail.files else False,  # بررسی وجود پیوست
        })

    # داده‌های ارسال‌شده به قالب
    context = {
        'report': daily_report,
        'blasting_details': daily_report.blasting_details.all(),
        'drilling_details': daily_report.drilling_details.all(),
        'loading_details': daily_report.loading_details.all(),
        'dump_details': daily_report.dump_details.all(),
        'stoppage_details': daily_report.stoppage_details.all(),
        'followup_details': followup_details,  # ارسال جزئیات پیگیری
        'inspection_details': daily_report.inspection_details.all(),
        'title': 'گزارش روزانه',
        'user_signature': user_signature,  # اضافه کردن امضا به کانتکست
    }

    # رندر قالب به HTML
    html_content = render_to_string('dailyreport_hse/daily_report_pdf.html', context)

    # تنظیم پاسخ HTTP برای PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="daily_report_{pk}.pdf"'

    # تولید PDF
    pdf_file = HTML(string=html_content, base_url=request.build_absolute_uri('/'))
    pdf_file.write_pdf(target=response)

    return response