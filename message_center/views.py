from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone
from datetime import timedelta
from permissions.utils import permission_required

from leave_reports.models import ShiftReport
from .models import ReminderLog
from .services import collect_pending_reminders
from .tasks import send_leave_reminders_task


def _counts():
    return {
        "pending_replacement": ShiftReport.objects.filter(
            status="pending_replacement", replacement_person__isnull=False
        ).count(),
        "pending_approval": ShiftReport.objects.filter(status="pending_approval").count(),
    }


@login_required
@permission_required("send_leave_reminders")
def leave_reminders(request):
    if request.method == "POST":
        role = request.POST.get("role")
        if role not in ("replacement", "manager", "all"):
            role = None
        task = send_leave_reminders_task.delay(role=role, actor_id=request.user.pk)
        messages.info(request, f"ارسال یادآوری‌ها در صف قرار گرفت (کد پیگیری: {task.id[:8]}…). نتیجه چند دقیقه دیگر در جدول لاگ نمایش داده می‌شود.")
        return redirect("message_center:leave_reminders")

    collection = collect_pending_reminders()
    recent_rate_limit = ReminderLog.objects.filter(
        error__contains="محدود", created_at__gte=timezone.now() - timedelta(hours=2)
    ).exists()
    context = {
        "counts": _counts(),
        "missing": collection["missing"][:20],
        "missing_count": len(collection["missing"]),
        "dedup_hours": getattr(settings, "PEYAMHUB_REMINDER_DEDUP_HOURS", 12),
        "send_delay": getattr(settings, "PEYAMHUB_SEND_DELAY_SECONDS", 4),
        "recent_rate_limit": recent_rate_limit,
        "logs": ReminderLog.objects.select_related("leave", "recipient", "triggered_by")[:50],
    }
    return render(request, "message_center/leave_reminders.html", context)
