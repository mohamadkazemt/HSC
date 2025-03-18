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

class MeetingListView(LoginRequiredMixin, ListView):
    model = Meeting
    template_name = 'meetings/meeting_list.html'
    context_object_name = 'meetings'
    ordering = ['-date', '-time']
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
def meeting_report(request):
    meetings = Meeting.objects.all()
    if not request.user.is_superuser:
        meetings = meetings.filter(participants=request.user)
    return render(request, 'meetings/meeting_report.html', {'meetings': meetings})

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
