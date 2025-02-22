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
import logging
from django.db import transaction
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.generic.edit import DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.contrib.auth.mixins import UserPassesTestMixin


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

            # Use a transaction to ensure atomicity
            with transaction.atomic():
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
                    block_id = blasting.get("block_id")
                    if block_id:  # Only create if block_id is provided
                        block = get_object_or_404(MiningBlock, id=block_id)
                        BlastingDetail.objects.create(
                            daily_report=daily_report,
                            explosion_occurred=blasting.get("explosion_occurred", False),
                            block=block,
                            description=blasting.get("description", ""),
                        )

                # ذخیره جزئیات حفاری
                for drilling in drilling_details:
                    block_id = drilling.get("block_id")
                    machine_id = drilling.get("machine_id")
                    if block_id and machine_id:  # Only create if both are provided
                        block = get_object_or_404(MiningBlock, id=block_id)
                        machine = get_object_or_404(
                            MiningMachine, id=machine_id
                        )
                        DrillingDetail.objects.create(
                            daily_report=daily_report,
                            block=block,
                            machine=machine,
                            status=drilling.get("status", None),  # Allow None
                            description=drilling.get("description", ""),
                        )

                # ذخیره جزئیات بارگیری
                for loading in loading_details:
                    block_id = loading.get("block_id")
                    machine_id = loading.get("machine_id")
                    if block_id and machine_id:
                        block = get_object_or_404(MiningBlock, id=block_id)
                        machine = get_object_or_404(
                            MiningMachine, id=machine_id
                        )
                        LoadingDetail.objects.create(
                            daily_report=daily_report,
                            block=block,
                            machine=machine,
                            status=loading.get("status", None),  # Allow None
                            description=loading.get("description", ""),
                        )

                # ذخیره جزئیات تخلیه
                for dump_detail in dump_details:
                    dump_id = dump_detail.get("dump_id")
                    if dump_id:
                        dump = get_object_or_404(Dump, id=dump_id)
                        DumpDetail.objects.create(
                            daily_report=daily_report,
                            dump=dump,
                            status=dump_detail.get("status", None),  # Allow None
                            description=dump_detail.get("description", ""),
                        )

                # ذخیره جزئیات توقف
                for stoppage in stoppage_details:  # Iterate through stoppage details
                    StoppageDetail.objects.create(
                        daily_report=daily_report,
                        reason=stoppage.get("reason", None),
                        start_time=stoppage.get("start_time", None),
                        end_time=stoppage.get("end_time", None),
                        description=stoppage.get("description", ""),
                    )

                # ذخیره جزئیات پیگیری
                index = 0 # فقط یک پیگیری در این مثال داریم
                description = received_data.get(f"followups[{index}][followup_description]")
                files = request.FILES.getlist(f"followups[{index}][followup_file]")

                # فقط یک بار ایجاد می‌کنیم
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
                        inspection=inspection.get("inspection", None),  # فیلد inspection رو اضافه کنید
                        status=inspection.get("status", None),
                        description=inspection.get("description", ""),
                    )

                return Response(
                    {"message": "گزارش با موفقیت ثبت شد.", "id": daily_report.id},
                    status=status.HTTP_201_CREATED,
                )

        except Exception as e:
            print(f"خطا: {e}")
            # If ANY error occurs within the transaction, it will be rolled back
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
        context['title'] = "ثبت گزارش‌های روزانه"
        return context








@class_permission_required("daily_report_list")
class DailyReportListView(LoginRequiredMixin, ListView):
    model = DailyReport
    template_name = "dailyreport_hse/daily_report_list.html"
    context_object_name = "daily_reports"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()

        # Get filter parameters from the request
        self.shift_filter = self.request.GET.get("shift", "")
        self.group_filter = self.request.GET.get("group", "")
        self.search_query = self.request.GET.get("search", "")

        # Apply filters
        if self.shift_filter and self.shift_filter != "همه":
            queryset = queryset.filter(shift=self.shift_filter)
        if self.group_filter and self.group_filter != "همه":
            queryset = queryset.filter(work_group=self.group_filter)

        # Apply search filter
        if self.search_query:
            queryset = queryset.filter(
                Q(user__username__icontains=self.search_query) |
                Q(user__first_name__icontains=self.search_query) |
                Q(user__last_name__icontains=self.search_query) |
                Q(user__userprofile__personnel_code__icontains=self.search_query) |
                Q(supervisor_comments__icontains=self.search_query) |
                Q(shift__icontains=self.search_query)
            )

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get the queryset (already filtered)
        queryset = self.get_queryset()

        # Paginate the queryset
        paginator = Paginator(queryset, self.paginate_by)
        page_number = self.request.GET.get('page')

        try:
            page_obj = paginator.get_page(page_number)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            page_obj = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            page_obj = paginator.page(paginator.num_pages)

        # Pass the paginated page object to the template
        context['daily_reports'] = page_obj

        # Pass the filter values to the template
        context["shift_filter"] = self.shift_filter
        context["group_filter"] = self.group_filter
        context["search_query"] = self.search_query
        context['title'] = "لیست گزارش‌های روزانه"


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
        context['title'] = 'جزئیات گزارش روزانه'

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

@class_permission_required("daily_report_delete")
class DailyReportDeleteView(LoginRequiredMixin, DeleteView):
    model = DailyReport
    success_url = '/dailyreport_hse/list/'
    
    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            self.object.delete()
            # حذف messages.success
            return JsonResponse({
                'status': 'success',
                'message': 'گزارش با موفقیت حذف شد'
            })
        except Exception as e:
            # حذف messages.error
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)