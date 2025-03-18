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
        if not self.request.user.is_superuser:
            queryset = queryset.filter(participants=self.request.user)
        return queryset

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
        form.instance.creator = self.request.user
        response = super().form_valid(form)
        MeetingService.send_notifications_to_all_users(self.object)
        messages.success(self.request, 'جلسه با موفقیت ایجاد شد.')
        return response

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
        response = super().form_valid(form)
        MeetingService.send_notifications_to_all_users(self.object)
        messages.success(self.request, 'جلسه با موفقیت بروزرسانی شد.')
        return response

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
            MeetingService.cancel_meeting(pk, request.user, reason)
            messages.success(request, 'جلسه با موفقیت لغو شد.')
            return redirect('meetings:meeting_list')
        except PermissionError as e:
            messages.error(request, str(e))
            return redirect('meetings:meeting_detail', pk=pk)
            
    return render(request, 'meetings/cancel_meeting.html', {
        'meeting': meeting,
        'title': 'لغو جلسه'
    })

def create_meeting(request):
    logger.debug("Entering create_meeting view function - Logging Test")

    if request.method == 'POST':
        form = MeetingForm(request.POST)

        logger.debug(f"Raw form data received: {request.POST}")
        logger.debug(f"Date value from form: {request.POST.get('date')}")

        # نمایش تاریخ دریافت شده از فرم در کنسول
        print(f"تاریخ دریافت شده از فرم: {request.POST.get('date')}")

        # نمایش فرمت های تاریخ مورد انتظار Django در کنسول
        print(f"فرمت‌های تاریخ مورد انتظار سرور: {settings.DATE_INPUT_FORMATS}")

        if form.is_valid():
            logger.info("Form is valid")
            logger.debug(f"Cleaned data: {form.cleaned_data}")
            logger.debug(f"Cleaned date: {form.cleaned_data.get('date')}")
            # بررسی فیلدهای اجباری
            if not form.cleaned_data.get('date'):
                form.add_error('date', 'لطفاً تاریخ جلسه را وارد کنید.')
            if not form.cleaned_data.get('start_time'):
                form.add_error('start_time', 'لطفاً زمان شروع جلسه را وارد کنید.')
            if not form.cleaned_data.get('end_time'):
                form.add_error('end_time', 'لطفاً زمان پایان جلسه را وارد کنید.')
            if not form.cleaned_data.get('location'):
                form.add_error('location', 'لطفاً مکان جلسه را وارد کنید.')
            if not form.cleaned_data.get('participants'):
                form.add_error('participants', 'لطفاً حداقل یک شرکت‌کننده را انتخاب کنید.')

            if not form.errors:
                logger.info(f"Cleaned data before save: {form.cleaned_data}")
                meeting = form.save(commit=False)
                meeting.creator = request.user
                meeting.save()
                form.save_m2m()  # برای ذخیره شرکت‌کنندگان
                messages.success(request, 'جلسه با موفقیت ایجاد شد.')
                logger.info(f"Meeting saved successfully. Meeting ID: {meeting.id}, Date: {meeting.date}")
                return redirect('meetings:meeting_list')
            else:
                 logger.warning(f"Form has errors: {form.errors}")
                 logger.warning(f"Form errors detail: {form.errors.as_data()}")
        else:
            logger.warning("Form is invalid")
            logger.warning(f"Form errors: {form.errors}")
            logger.warning(f"Form errors detail: {form.errors.as_data()}")
    else:
        form = MeetingForm()
    return render(request, 'meetings/meeting_form.html', {'form': form})


@login_required
def delete_meeting(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)
    
    if request.method == 'POST':
        # ارسال نوتیفیکیشن به شرکت‌کنندگان
        for participant in meeting.participants.all():
            Notification.objects.create(
                recipient=participant,
                title='حذف جلسه',
                message=f'جلسه "{meeting.title}" حذف شده است.',
                notification_type='meeting'
            )
        
        meeting.delete()
        messages.success(request, 'جلسه با موفقیت حذف شد.')
        return redirect('meetings:meeting_list')
    
    return render(request, 'meetings/meeting_confirm_delete.html', {'meeting': meeting})

@login_required
def meeting_export(request):
    meetings = Meeting.objects.all().order_by('-date', '-start_time')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="meetings.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['عنوان', 'تاریخ', 'زمان شروع', 'زمان پایان', 'مکان', 'تعداد شرکت‌کنندگان', 'توضیحات'])
    
    for meeting in meetings:
        writer.writerow([
            meeting.title,
            meeting.date,
            meeting.start_time,
            meeting.end_time,
            meeting.location,
            meeting.participants.count(),
            meeting.description
        ])
    
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
