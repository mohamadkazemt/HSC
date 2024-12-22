from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
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


logger = logging.getLogger(__name__)






class CreateDailyReportView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            print("Incoming Data:", request.data)
            print("Incoming Files:", request.FILES)


            # دریافت داده‌های اصلی
            blasting_details = json.loads(request.data.get("blasting_details", "[]"))
            drilling_details = json.loads(request.data.get("drilling_details", "[]"))
            loading_details = json.loads(request.data.get("loading_details", "[]"))
            dump_details = json.loads(request.data.get("dump_details", "[]"))
            stoppage_details = json.loads(request.data.get("stoppage_details", "[]"))
            inspection_details = json.loads(request.data.get("inspection_details", "[]"))
            followup_details = json.loads(request.data.get("followup_details", "[]"))
            print("Followup Details Received:", followup_details)
            print("Files Received:", request.FILES)
            # دریافت شیفت و گروه کاری جاری
            current_shift, current_group = get_current_shift_and_group()

            if not current_shift or not current_group:
                return Response({"error": "شیفت یا گروه کاری جاری شناسایی نشد."}, status=status.HTTP_400_BAD_REQUEST)

            # ایجاد گزارش روزانه
            daily_report = DailyReport.objects.create(
                user=request.user,
                shift=current_shift,  # مقدار شیفت از `get_current_shift_and_group`
                work_group=current_group,
                supervisor_comments=request.data.get("supervisor_comments", "")
            )

            # ذخیره جزئیات آتشباری
            for blasting in blasting_details:
                if blasting.get("block_id"):
                    block = get_object_or_404(MiningBlock, id=blasting.get("block_id"))
                    BlastingDetail.objects.create(
                        daily_report=daily_report,
                        explosion_occurred=blasting.get("explosion_occurred", False),
                        block=block,
                        description=blasting.get("description", "")
                    )

            # ذخیره جزئیات حفاری
            for drilling in drilling_details:
                if drilling.get("block_id") and drilling.get("machine_id"):
                    block = get_object_or_404(MiningBlock, id=drilling.get("block_id"))
                    machine = get_object_or_404(MiningMachine, id=drilling.get("machine_id"))
                    DrillingDetail.objects.create(
                        daily_report=daily_report,
                        block=block,
                        machine=machine,
                        status=drilling.get("status", "unknown")
                    )

            # ذخیره جزئیات بارگیری
            for loading in loading_details:
                if loading.get("block_id") and loading.get("machine_id"):
                    block = get_object_or_404(MiningBlock, id=loading.get("block_id"))
                    machine = get_object_or_404(MiningMachine, id=loading.get("machine_id"))
                    LoadingDetail.objects.create(
                        daily_report=daily_report,
                        block=block,
                        machine=machine,
                        status=loading.get("status", "unknown")
                    )

            # ذخیره جزئیات تخلیه
            for dump_detail in dump_details:
                if dump_detail.get("dump_id"):
                    dump = get_object_or_404(Dump, id=dump_detail.get("dump_id"))
                    DumpDetail.objects.create(
                        daily_report=daily_report,
                        dump=dump,
                        status=dump_detail.get("status", "unknown"),
                        description=dump_detail.get("description", "")
                    )

            # ذخیره جزئیات توقفات
            for stoppage in stoppage_details:
                if stoppage.get("reason"):
                     StoppageDetail.objects.create(
                        daily_report=daily_report,
                        reason=stoppage.get("reason"),
                        start_time=stoppage.get("start_time"),
                        end_time=stoppage.get("end_time"),
                        description=stoppage.get("description", "")
                    )

            # ذخیره جزئیات پیگیری
            followup_index = 0
            while f"followup_description_{followup_index}" in request.POST:
                description = request.POST.get(f"followup_description_{followup_index}", "")
                followup_instance = FollowupDetail.objects.create(
                    daily_report=daily_report,
                    description=description
                )

                # بررسی و ذخیره فایل‌ها
                file_index = 0
                while f"followup_file_{followup_index}_{file_index}" in request.FILES:
                    file = request.FILES[f"followup_file_{followup_index}_{file_index}"]
                    followup_instance.files.save(file.name, file)
                    file_index += 1

                followup_index += 1
            print("Followup Description Keys:", [key for key in request.POST.keys() if "followup_description" in key])
            print("Followup File Keys:", [key for key in request.FILES.keys()])

            # ذخیره جزئیات بازرسی
            for inspection in inspection_details:
                InspectionDetail.objects.create(
                    daily_report=daily_report,
                    inspection_done=inspection.get("inspection_done", False),
                    status=inspection.get("status", "unknown"),
                    description=inspection.get("description", "")
                )

            return Response({"message": "گزارش با موفقیت ثبت شد.", "id": daily_report.id}, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"خطا: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





class DailyReportFormView(LoginRequiredMixin, TemplateView):
    template_name = "dailyreport_hse/create_shift_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mining_blocks'] = MiningBlock.objects.all()
        context['mining_machines'] = MiningMachine.objects.all()
        context['dumps'] = Dump.objects.all()
        return context





class DailyReportListView(ListView):
    model = DailyReport
    template_name = "dailyreport_hse/daily_report_list.html"
    context_object_name = "daily_reports"
    paginate_by = 10  # تعداد گزارش‌ها در هر صفحه

    def get_queryset(self):
        queryset = super().get_queryset()

        # فیلترها
        shift = self.request.GET.get("shift", "همه")
        group = self.request.GET.get("group", "همه")
        search_query = self.request.GET.get("search", "")

        if shift != "همه":
            queryset = queryset.filter(shift=shift)

        if group != "همه":
            queryset = queryset.filter(work_group=group)

        if search_query:
            queryset = queryset.filter(
                Q(user__username__icontains=search_query) |
                Q(supervisor_comments__icontains=search_query) |
                Q(shift__icontains=search_query)
            )

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['shift_filter'] = self.request.GET.get("shift", "همه")
        context['group_filter'] = self.request.GET.get("group", "همه")
        context['search_query'] = self.request.GET.get("search", "")
        return context






class DailyReportDetailView(DetailView):
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

        return context