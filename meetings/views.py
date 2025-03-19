from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from .models import Meeting
from .forms import MeetingForm
from .services import MeetingService
from dashboard.models import Notification
from django.http import HttpResponse
import csv
from django.db.models import Q
from django.conf import settings
import logging
# from jalalidate import JalaliDate as jdate  # امتحان import از jalalidate (بدون آندرلاین)
import jdatetime
from django.utils import timezone
from .sms_utils import send_meeting_cancelled_sms, send_meeting_reminder_sms, send_meeting_updated_sms, send_meeting_deleted_sms, send_meeting_created_sms

logger = logging.getLogger(__name__)
logger.debug("Logging system is initialized in meetings/views.py")

class MeetingListView(LoginRequiredMixin, ListView):
    model = Meeting
    template_name = 'meetings/meeting_list.html'
    context_object_name = 'meetings'
    ordering = ['-date', '-start_time']
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # اعمال فیلترها
        q = self.request.GET.get('q')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        location = self.request.GET.get('location')
        status = self.request.GET.get('status')

        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(location__icontains=q) |
                Q(participants__first_name__icontains=q) |
                Q(participants__last_name__icontains=q)
            ).distinct()

        # تبدیل تاریخ شمسی به میلادی و اعمال فیلتر
        try:
            if start_date:
                print(f"تاریخ شروع دریافتی: {start_date}")
                # تبدیل تاریخ شمسی به میلادی
                year, month, day = map(int, start_date.split('/'))
                j_date = jdatetime.date(year, month, day)
                g_date = j_date.togregorian()
                print(f"تاریخ شروع میلادی: {g_date}")
                queryset = queryset.filter(date__gte=g_date)
        except (ValueError, TypeError) as e:
            print(f"خطا در تبدیل تاریخ شروع: {e}")

        try:
            if end_date:
                print(f"تاریخ پایان دریافتی: {end_date}")
                # تبدیل تاریخ شمسی به میلادی
                year, month, day = map(int, end_date.split('/'))
                j_date = jdatetime.date(year, month, day)
                g_date = j_date.togregorian()
                print(f"تاریخ پایان میلادی: {g_date}")
                queryset = queryset.filter(date__lte=g_date)
        except (ValueError, TypeError) as e:
            print(f"خطا در تبدیل تاریخ پایان: {e}")
        
        if location:
            queryset = queryset.filter(location__icontains=location)
        
        if status:
            queryset = queryset.filter(status=status)

        # فیلتر دسترسی کاربر
        if not self.request.user.is_superuser:
            queryset = queryset.filter(participants=self.request.user)

        return queryset.order_by('-date', '-start_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # اضافه کردن آمار به context
        context['total_meetings'] = self.get_queryset().count()
        context['total_participants'] = sum(meeting.participants.count() for meeting in self.get_queryset())
        if context['total_meetings'] > 0:
            context['avg_participants'] = round(context['total_participants'] / context['total_meetings'], 2)
        else:
            context['avg_participants'] = 0
        return context

class MeetingDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Meeting
    template_name = 'meetings/meeting_detail.html'
    context_object_name = 'meeting'

    def test_func(self):
        meeting = self.get_object()
        return self.request.user.is_superuser or self.request.user in meeting.participants.all()

class MeetingCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Meeting
    form_class = MeetingForm
    template_name = 'meetings/meeting_form.html'
    success_url = reverse_lazy('meetings:meeting_list')

    def test_func(self):
        content_type = ContentType.objects.get_for_model(Meeting)
        permission = Permission.objects.get(content_type=content_type, codename='add_meeting')
        return self.request.user.has_perm('meetings.add_meeting')

    def form_valid(self, form):
        print("\n=== شروع ایجاد جلسه در view ===")
        try:
            meeting = MeetingService.create_meeting(
                title=form.cleaned_data['title'],
                date=form.cleaned_data['date'],
                start_time=form.cleaned_data['start_time'],
                end_time=form.cleaned_data['end_time'],
                creator=self.request.user,
                participants=form.cleaned_data['participants'],
                manual_numbers=form.cleaned_data.get('manual_numbers', ''),
                notify_transport_coordinator=form.cleaned_data.get('notify_transport_coordinator', False)
            )
            print(f"جلسه با شناسه {meeting.id} با موفقیت ایجاد شد")

            messages.success(self.request, 'جلسه با موفقیت ایجاد شد.')
            return redirect('meetings:meeting_list')
        except Exception as e:
            print(f"خطا در ایجاد جلسه: {str(e)}")
            messages.error(self.request, f'خطا در ایجاد جلسه: {str(e)}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        logger.warning("Form is invalid")
        logger.warning(f"Form errors: {form.errors}")
        logger.warning(f"Form errors detail: {form.errors.as_data()}")
        
        # نمایش خطاهای عمومی
        if form.non_field_errors():
            for error in form.non_field_errors():
                messages.error(self.request, error)
        
        # نمایش خطاهای فیلدها
        for field, errors in form.errors.items():
            if field != '__all__':  # خطاهای عمومی را نادیده می‌گیریم
                for error in errors:
                    messages.error(self.request, f"{form.fields[field].label}: {error}")
        
        return super().form_invalid(form)

class MeetingUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Meeting
    form_class = MeetingForm
    template_name = 'meetings/meeting_form.html'
    success_url = reverse_lazy('meetings:meeting_list')

    def test_func(self):
        content_type = ContentType.objects.get_for_model(Meeting)
        permission = Permission.objects.get(content_type=content_type, codename='change_meeting')
        return self.request.user.has_perm('meetings.change_meeting')

    def form_valid(self, form):
        try:
            print("\n=== شروع بروزرسانی جلسه ===")
            meeting = form.save()
            print(f"جلسه با شناسه {meeting.id} با موفقیت بروزرسانی شد")
            
            # ارسال پیامک بروزرسانی به شرکت‌کنندگان
            for participant in meeting.participants.all():
                if hasattr(participant, 'userprofile') and participant.userprofile.mobile:
                    print(f"ارسال پیامک بروزرسانی به شماره {participant.userprofile.mobile}")
                    send_meeting_updated_sms(
                        participant.userprofile.mobile,
                        meeting.id,
                        meeting.title,
                        meeting.date,
                        meeting.start_time
                    )
            
            # ارسال پیامک بروزرسانی به شماره‌های دستی
            if meeting.manual_numbers:
                numbers = meeting.manual_numbers.split('\n')
                for number in numbers:
                    if number.strip():
                        print(f"ارسال پیامک بروزرسانی به شماره دستی {number.strip()}")
                        send_meeting_updated_sms(
                            number.strip(),
                            meeting.id,
                            meeting.title,
                            meeting.date,
                            meeting.start_time
                        )
            
            # ارسال پیامک بروزرسانی به هماهنگ‌کننده حمل و نقل
            if meeting.notify_transport_coordinator:
                coordinators = MeetingService.get_transport_coordinators()
                for coordinator in coordinators:
                    if hasattr(coordinator, 'userprofile') and coordinator.userprofile.mobile:
                        print(f"ارسال پیامک بروزرسانی به هماهنگ‌کننده حمل و نقل {coordinator.userprofile.mobile}")
                        send_meeting_updated_sms(
                            coordinator.userprofile.mobile,
                            meeting.id,
                            meeting.title,
                            meeting.date,
                            meeting.start_time
                        )
            
            messages.success(self.request, 'جلسه با موفقیت بروزرسانی شد.')
            return redirect('meetings:meeting_list')
            
        except Exception as e:
            print(f"خطا در بروزرسانی جلسه: {str(e)}")
            import traceback
            print(f"جزئیات خطا: {traceback.format_exc()}")
            messages.error(self.request, 'خطا در بروزرسانی جلسه. لطفاً دوباره تلاش کنید.')
            return self.form_invalid(form)

class MeetingDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Meeting
    template_name = 'meetings/meeting_confirm_delete.html'
    success_url = reverse_lazy('meetings:meeting_list')

    def test_func(self):
        content_type = ContentType.objects.get_for_model(Meeting)
        permission = Permission.objects.get(content_type=content_type, codename='delete_meeting')
        return self.request.user.has_perm('meetings.delete_meeting')

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, 'جلسه با موفقیت حذف شد.')
        return response

@login_required
def meeting_list(request):
    meetings = Meeting.objects.all().order_by('-date', '-start_time')
    return render(request, 'meetings/meeting_list.html', {'meetings': meetings})

@login_required
def meeting_report(request):
    meetings = Meeting.objects.all().order_by('-date', '-start_time')
    
    # محاسبه آمار
    total_meetings = meetings.count()
    total_participants = sum(meeting.participants.count() for meeting in meetings)
    avg_participants = total_participants / total_meetings if total_meetings > 0 else 0
    
    # گروه‌بندی جلسات بر اساس تاریخ
    meetings_by_date = {}
    for meeting in meetings:
        date = meeting.date
        if date not in meetings_by_date:
            meetings_by_date[date] = []
        meetings_by_date[date].append(meeting)
    
    context = {
        'meetings': meetings,
        'total_meetings': total_meetings,
        'total_participants': total_participants,
        'avg_participants': round(avg_participants, 2),
        'meetings_by_date': meetings_by_date
    }
    
    return render(request, 'meetings/meeting_report.html', context)

@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('meetings:meeting_list')

@login_required
def cancel_meeting(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)
    
    if request.method == 'POST':
        reason = request.POST.get('cancellation_reason')
        if not reason:
            messages.error(request, 'لطفاً دلیل لغو جلسه را وارد کنید.')
            return redirect('meetings:meeting_detail', pk=pk)
            
        try:
            print("\n=== شروع لغو جلسه ===")
            print(f"شناسه جلسه: {meeting.id}")
            print(f"عنوان جلسه: {meeting.title}")
            print(f"دلیل لغو: {reason}")
            
            # ارسال پیامک به شرکت‌کنندگان
            for participant in meeting.participants.all():
                if hasattr(participant, 'userprofile') and participant.userprofile.mobile:
                    print(f"ارسال پیامک لغو به شماره {participant.userprofile.mobile}")
                    send_meeting_cancelled_sms(
                        participant.userprofile.mobile,
                        meeting.id,
                        meeting.title,
                        meeting.date,
                        meeting.start_time,
                        reason
                    )
            
            # ارسال پیامک به شماره‌های دستی
            if meeting.manual_numbers:
                numbers = meeting.manual_numbers.split('\n')
                for number in numbers:
                    if number.strip():
                        print(f"ارسال پیامک لغو به شماره دستی {number.strip()}")
                        send_meeting_cancelled_sms(
                            number.strip(),
                            meeting.id,
                            meeting.title,
                            meeting.date,
                            meeting.start_time,
                            reason
                        )
            
            # ارسال پیامک به هماهنگ‌کننده حمل و نقل
            if meeting.notify_transport_coordinator:
                coordinators = MeetingService.get_transport_coordinators()
                for coordinator in coordinators:
                    if hasattr(coordinator, 'userprofile') and coordinator.userprofile.mobile:
                        print(f"ارسال پیامک لغو به هماهنگ‌کننده حمل و نقل {coordinator.userprofile.mobile}")
                        send_meeting_cancelled_sms(
                            coordinator.userprofile.mobile,
                            meeting.id,
                            meeting.title,
                            meeting.date,
                            meeting.start_time,
                            reason
                        )
            
            # لغو جلسه
            meeting.status = 'cancelled'
            meeting.cancellation_reason = reason
            meeting.cancelled_by = request.user
            meeting.cancelled_at = timezone.now()
            meeting.save()
            
            print("جلسه با موفقیت لغو شد")
            messages.success(request, 'جلسه با موفقیت لغو شد.')
            return redirect('meetings:meeting_list')
            
        except Exception as e:
            print(f"خطا در لغو جلسه: {str(e)}")
            import traceback
            print(f"جزئیات خطا: {traceback.format_exc()}")
            messages.error(request, 'خطا در لغو جلسه. لطفاً دوباره تلاش کنید.')
            return redirect('meetings:meeting_detail', pk=pk)
            
    return render(request, 'meetings/cancel_meeting.html', {
        'meeting': meeting,
        'title': 'لغو جلسه'
    })

@login_required
def delete_meeting(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)
    
    if request.method == 'POST':
        try:
            print("\n=== شروع حذف جلسه ===")
            print(f"شناسه جلسه: {meeting.id}")
            print(f"عنوان جلسه: {meeting.title}")
            
            # ارسال پیامک حذف به شرکت‌کنندگان
            for participant in meeting.participants.all():
                if hasattr(participant, 'userprofile') and participant.userprofile.mobile:
                    print(f"ارسال پیامک حذف به شماره {participant.userprofile.mobile}")
                    send_meeting_deleted_sms(
                        participant.userprofile.mobile,
                        meeting.id,
                        meeting.title,
                        meeting.date,
                        meeting.start_time
                    )
            
            # ارسال پیامک حذف به شماره‌های دستی
            if meeting.manual_numbers:
                numbers = meeting.manual_numbers.split('\n')
                for number in numbers:
                    if number.strip():
                        print(f"ارسال پیامک حذف به شماره دستی {number.strip()}")
                        send_meeting_deleted_sms(
                            number.strip(),
                            meeting.id,
                            meeting.title,
                            meeting.date,
                            meeting.start_time
                        )
            
            # ارسال پیامک حذف به هماهنگ‌کننده حمل و نقل
            if meeting.notify_transport_coordinator:
                coordinators = MeetingService.get_transport_coordinators()
                for coordinator in coordinators:
                    if hasattr(coordinator, 'userprofile') and coordinator.userprofile.mobile:
                        print(f"ارسال پیامک حذف به هماهنگ‌کننده حمل و نقل {coordinator.userprofile.mobile}")
                        send_meeting_deleted_sms(
                            coordinator.userprofile.mobile,
                            meeting.id,
                            meeting.title,
                            meeting.date,
                            meeting.start_time
                        )
            
            # ارسال نوتیفیکیشن به شرکت‌کنندگان
            for participant in meeting.participants.all():
                Notification.objects.create(
                    recipient=participant,
                    title='حذف جلسه',
                    message=f'جلسه "{meeting.title}" حذف شده است.',
                    notification_type='meeting'
                )
            
            meeting.delete()
            print("جلسه با موفقیت حذف شد")
            messages.success(request, 'جلسه با موفقیت حذف شد.')
            return redirect('meetings:meeting_list')
            
        except Exception as e:
            print(f"خطا در حذف جلسه: {str(e)}")
            import traceback
            print(f"جزئیات خطا: {traceback.format_exc()}")
            messages.error(request, 'خطا در حذف جلسه. لطفاً دوباره تلاش کنید.')
            return redirect('meetings:meeting_detail', pk=pk)
    
    return render(request, 'meetings/meeting_confirm_delete.html', {'meeting': meeting})

@login_required
def meeting_export(request):
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill
    from io import BytesIO
    
    # ایجاد یک فایل اکسل جدید
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "لیست جلسات"
    
    # تنظیم عنوان‌های ستون‌ها
    headers = ['عنوان', 'تاریخ', 'زمان شروع', 'زمان پایان', 'مکان', 'شرکت‌کنندگان', 'وضعیت', 'توضیحات']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col)
        cell.value = header
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
        cell.alignment = Alignment(horizontal='center')
    
    # دریافت جلسات و مرتب‌سازی
    meetings = Meeting.objects.all().order_by('-date', '-start_time')
    
    # پر کردن داده‌ها
    for row, meeting in enumerate(meetings, 2):
        # تبدیل تاریخ میلادی به شمسی
        j_date = jdatetime.date.fromgregorian(date=meeting.date)
        formatted_date = j_date.strftime("%Y/%m/%d")
        
        # وضعیت جلسه به فارسی
        status_map = {
            'scheduled': 'برنامه‌ریزی شده',
            'cancelled': 'لغو شده',
            'completed': 'برگزار شده'
        }
        
        # لیست شرکت‌کنندگان
        participants = ", ".join([f"{p.get_full_name()}" for p in meeting.participants.all()])
        
        # مقادیر ستون‌ها
        values = [
            meeting.title,
            formatted_date,
            meeting.start_time.strftime("%H:%M"),
            meeting.end_time.strftime("%H:%M"),
            meeting.location,
            participants,
            status_map.get(meeting.status, meeting.status),
            meeting.description
        ]
        
        for col, value in enumerate(values, 1):
            cell = ws.cell(row=row, column=col)
            cell.value = value
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    
    # تنظیم عرض ستون‌ها
    for column in ws.columns:
        max_length = 0
        column_letter = openpyxl.utils.get_column_letter(column[0].column)
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column_letter].width = adjusted_width if adjusted_width < 50 else 50
    
    # ذخیره فایل
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="meetings.xlsx"'
    
    # ذخیره به بایت‌استریم
    wb.save(response)
    return response

@login_required
def meeting_calendar(request):
    meetings = Meeting.objects.all().order_by('date', 'start_time')
    
    # تبدیل جلسات به فرمت مناسب برای تقویم
    events = []
    for meeting in meetings:
        events.append({
            'id': meeting.pk,
            'title': meeting.title,
            'start': f"{meeting.date}T{meeting.start_time}",
            'end': f"{meeting.date}T{meeting.end_time}",
            'location': meeting.location,
            'participants': [p.get_full_name() for p in meeting.participants.all()],
            'description': meeting.description
        })
    
    return render(request, 'meetings/meeting_calendar.html', {'events': events})

@login_required
def meeting_search(request):
    query = request.GET.get('q', '')
    meetings = Meeting.objects.all()
    
    if query:
        meetings = meetings.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query) |
            Q(participants__first_name__icontains=query) |
            Q(participants__last_name__icontains=query)
        ).distinct()
    
    meetings = meetings.order_by('-date', '-start_time')
    return render(request, 'meetings/meeting_list.html', {'meetings': meetings, 'query': query})

@login_required
def meeting_filter(request):
    meetings = Meeting.objects.all()
    
    # فیلتر بر اساس تاریخ
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        meetings = meetings.filter(date__gte=start_date)
    if end_date:
        meetings = meetings.filter(date__lte=end_date)
    
    # فیلتر بر اساس مکان
    location = request.GET.get('location')
    if location:
        meetings = meetings.filter(location__icontains=location)
    
    # فیلتر بر اساس شرکت‌کننده
    participant = request.GET.get('participant')
    if participant:
        meetings = meetings.filter(participants__id=participant)
    
    meetings = meetings.order_by('-date', '-start_time')
    return render(request, 'meetings/meeting_list.html', {'meetings': meetings})
