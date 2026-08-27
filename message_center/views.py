import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from datetime import timedelta
from permissions.utils import permission_required

from leave_reports.models import ShiftReport
from .models import Broadcast, BroadcastRecipient, MessageTemplate, ReminderLog
from .services import collect_pending_reminders

logger = logging.getLogger(__name__)
from .tasks import send_leave_reminders_task, send_broadcast_task


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


# ---------------------------------------------------------------------------
# ارسال پیام گروهی
# ---------------------------------------------------------------------------

def _parse_list_text(raw: str):
    """تبدیل متن چندخطی (شماره/کد پرسنلی) به لیست تمیز."""
    items = []
    for line in (raw or "").splitlines():
        item = line.strip()
        if item:
            items.append(item)
    return items


def _parse_uploaded_file(file_obj):
    """خواندن فایل CSV/TXT و استخراج شماره‌ها/کدهای پرسنلی."""
    if not file_obj:
        return []
    data = file_obj.read().decode("utf-8-sig", errors="ignore")
    items = []
    for line in data.splitlines():
        line = line.strip()
        if not line:
            continue
        # جداکننده ویرگول/تب برای ستون اول
        for sep in (",", "\t", ";"):
            if sep in line:
                line = line.split(sep)[0].strip()
                break
        if line:
            items.append(line)
    return items


@login_required
@permission_required("message_broadcast_send")
def broadcast_compose(request):
    """صفحه ترکیب‌کننده پیام گروهی (شماره موبایل / کد پرسنلی / قالب)."""
    templates = MessageTemplate.objects.filter(is_active=True).order_by("-updated_at")
    context = {
        "templates": templates,
        "channels": Broadcast.Channel.choices,
    }
    return render(request, "message_center/broadcast_compose.html", context)


@login_required
@permission_required("message_broadcast_send")
def broadcast_preview(request):
    """مرحله پیش‌نمایش: تشخیص گیرنده‌ها و نمایش لیست برای تأیید نهایی."""
    if request.method != "POST":
        return redirect("message_center:broadcast_compose")

    text = (request.POST.get("text") or "").strip()
    channel = request.POST.get("channel") or Broadcast.Channel.SMS
    title = (request.POST.get("title") or "").strip()

    mobile_raw = request.POST.get("mobile_numbers", "")
    personnel_raw = request.POST.get("personnel_codes", "")
    mobile_numbers = _parse_list_text(mobile_raw)
    personnel_codes = _parse_list_text(personnel_raw)

    # فایل آپلودی
    uploaded = request.FILES.get("recipient_file")
    if uploaded:
        file_items = _parse_uploaded_file(uploaded)
        # حدس: اگر عدد ۱۰ رقمی بود موبایل، وگرنه کد پرسنلی
        for item in file_items:
            digits = "".join(ch for ch in item if ch.isdigit())
            if len(digits) in (10, 11, 12, 13) and len(digits) >= 10:
                mobile_numbers.append(item)
            else:
                personnel_codes.append(item)

    # کدهای پرسنلی انتخاب‌شده از لیست
    selected_personnel = request.POST.getlist("selected_personnel")
    if not personnel_codes:
        personnel_codes = list(selected_personnel) if selected_personnel else []

    if not text:
        messages.error(request, "متن پیام نباید خالی باشد.")
        return redirect("message_center:broadcast_compose")
    if not mobile_numbers and not personnel_codes:
        messages.error(request, "حداقل یک گیرنده (شماره موبایل یا کد پرسنلی) وارد کنید.")
        return redirect("message_center:broadcast_compose")

    # ذخیره پیش‌نویس و تشخیص گیرنده‌ها
    broadcast = Broadcast.objects.create(
        title=title,
        text=text,
        channel=channel if channel in (Broadcast.Channel.SMS, Broadcast.Channel.RUBIKA) else Broadcast.Channel.SMS,
        mobile_numbers=mobile_numbers,
        personnel_codes=personnel_codes,
        source_file_name=uploaded.name if uploaded else "",
        created_by=request.user,
        status=Broadcast.Status.DRAFT,
    )

    from .broadcast_service import prepare_broadcast

    resolved = prepare_broadcast(broadcast)

    # پاک‌کردن پیش‌نویس‌های قدیمی این کاربر (اختیاری)
    context = {
        "broadcast": broadcast,
        "recipients": resolved,
        "ok_count": broadcast.recipients_resolved,
        "invalid_count": broadcast.recipients_invalid,
    }
    return render(request, "message_center/broadcast_preview.html", context)


@login_required
@permission_required("message_broadcast_send")
def broadcast_send(request, broadcast_id):
    """تأیید و ارسال/زمان‌بندی نهایی پیام گروهی."""
    broadcast = get_object_or_404(Broadcast, pk=broadcast_id)

    if request.method != "POST":
        return redirect("message_center:broadcast_list")

    # ثبت اعلان درون‌برنامه‌ای (اختیاری)
    also_notify = request.POST.get("also_notify") == "1"

    schedule_raw = (request.POST.get("scheduled_for") or "").strip()
    scheduled_for = None
    if schedule_raw:
        try:
            from django.utils.dateparse import parse_datetime
            parsed = parse_datetime(schedule_raw.replace("T", "T"))
            if parsed is None:
                # فرمت بدون ثانیه
                parsed = parse_datetime(schedule_raw + ":00")
            if parsed:
                scheduled_for = parsed
        except Exception:
            scheduled_for = None

    from .broadcast_service import execute_broadcast, mark_invalid_recipients_canceled

    mark_invalid_recipients_canceled(broadcast)

    if scheduled_for:
        broadcast.status = Broadcast.Status.SCHEDULED
        broadcast.scheduled_for = scheduled_for
        broadcast.save(update_fields=["status", "scheduled_for"])

        # برنامه‌ریزی ارسال با ETA
        try:
            send_broadcast_task.apply_async(
                args=[broadcast.pk], eta=scheduled_for, serializer="json"
            )
        except Exception:
            # بروکر (Redis/Celery) در دسترس نیست؛ به‌صورت هم‌زمان ارسال کن
            logger.exception("Broker unavailable for scheduled broadcast %s; sending sync", broadcast.pk)
            broadcast.status = Broadcast.Status.RESOLVED
            broadcast.scheduled_for = None
            broadcast.save(update_fields=["status", "scheduled_for"])
            try:
                execute_broadcast(broadcast)
            except Exception as exc:
                logger.exception("Sync broadcast %s failed", broadcast.pk)
                messages.error(request, f"خطا در ارسال: {exc}")
                return redirect("message_center:broadcast_list")

        if also_notify and broadcast.recipients_resolved:
            _create_notifications(broadcast)

        messages.success(
            request,
            f"ارسال برای ساعت {scheduled_for:%Y/%m/%d %H:%M} زمان‌بندی شد.",
        )
        return redirect("message_center:broadcast_list")

    # ارسال فوری
    try:
        send_broadcast_task.delay(broadcast.pk)
    except Exception:
        # بروکر در دسترس نیست؛ ارسال هم‌زمان
        logger.exception("Broker unavailable for broadcast %s; sending sync", broadcast.pk)
        try:
            broadcast.status = Broadcast.Status.RESOLVED
            broadcast.save(update_fields=["status"])
            execute_broadcast(broadcast)
        except Exception as exc:
            logger.exception("Sync broadcast %s failed", broadcast.pk)
            messages.error(request, f"خطا در ارسال: {exc}")
            return redirect("message_center:broadcast_list")
        else:
            messages.success(
                request,
                f"ارسال {broadcast.recipients_resolved} گیرنده انجام شد (ذخیره محلی).",
            )
            return redirect("message_center:broadcast_list")

    if also_notify and broadcast.recipients_resolved:
        _create_notifications(broadcast)

    messages.success(
        request,
        f"ارسال {broadcast.recipients_resolved} گیرنده در صف قرار گرفت.",
    )
    return redirect("message_center:broadcast_list")


def _create_notifications(broadcast):
    """ایجاد اعلان درون‌برنامه‌ای برای گیرنده‌های دارای کاربر."""
    from dashboard.tasks import create_notification_task

    for rec in broadcast.recipients.filter(
        resolve_status=BroadcastRecipient.ResolveStatus.OK, user__isnull=False
    ):
        create_notification_task.delay(
            rec.user_id,
            broadcast.title or "پیام گروهی",
            broadcast.text[:200],
            "info",
            None,
        )


@login_required
@permission_required("message_broadcast_send")
def broadcast_cancel(request, broadcast_id):
    """لغو یک پیام گروهی که زمان‌بندی شده/در انتظار است."""
    broadcast = get_object_or_404(Broadcast, pk=broadcast_id)
    if request.method == "POST":
        if broadcast.status in (
            Broadcast.Status.DRAFT,
            Broadcast.Status.RESOLVED,
            Broadcast.Status.SCHEDULED,
        ):
            broadcast.status = Broadcast.Status.CANCELLED
            broadcast.save(update_fields=["status"])
            broadcast.recipients.update(send_status=BroadcastRecipient.SendStatus.CANCELED)
            messages.success(request, "پیام گروهی لغو شد.")
        else:
            messages.warning(request, "این پیام قابل لغو نیست.")
    return redirect("message_center:broadcast_list")


@login_required
@permission_required("message_broadcast_send")
def broadcast_list(request):
    """فهرست پیام‌های گروهی با وضعیت ارسال."""
    broadcasts = Broadcast.objects.select_related("created_by").order_by("-created_at")
    query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "")
    if query:
        broadcasts = broadcasts.filter(Q(title__icontains=query) | Q(text__icontains=query))
    if status_filter in dict(Broadcast.Status.choices):
        broadcasts = broadcasts.filter(status=status_filter)

    counts = {
        "all": Broadcast.objects.count(),
        "scheduled": Broadcast.objects.filter(status=Broadcast.Status.SCHEDULED).count(),
        "completed": Broadcast.objects.filter(
            status__in=[Broadcast.Status.COMPLETED, Broadcast.Status.PARTIAL]
        ).count(),
        "failed": Broadcast.objects.filter(status=Broadcast.Status.FAILED).count(),
    }

    context = {
        "broadcasts": broadcasts[:100],
        "query": query,
        "status_filter": status_filter,
        "counts": counts,
        "status_choices": Broadcast.Status.choices,
    }
    return render(request, "message_center/broadcast_list.html", context)


@login_required
@permission_required("message_broadcast_send")
def broadcast_detail(request, broadcast_id):
    """جزئیات و لاگ گیرنده‌های یک پیام گروهی."""
    broadcast = get_object_or_404(Broadcast, pk=broadcast_id)
    recipients = broadcast.recipients.select_related("user").order_by("-id")
    status_filter = request.GET.get("status", "")
    if status_filter:
        recipients = recipients.filter(send_status=status_filter)

    context = {
        "broadcast": broadcast,
        "recipients": recipients,
        "status_filter": status_filter,
        "send_status_choices": BroadcastRecipient.SendStatus.choices,
        "stats": {
            "resolved": broadcast.recipients_resolved,
            "invalid": broadcast.recipients_invalid,
            "sent": broadcast.recipients.filter(send_status=BroadcastRecipient.SendStatus.SENT).count(),
            "failed": broadcast.recipients.filter(send_status=BroadcastRecipient.SendStatus.FAILED).count(),
            "pending": broadcast.recipients.filter(send_status=BroadcastRecipient.SendStatus.PENDING).count(),
        },
    }
    return render(request, "message_center/broadcast_detail.html", context)


@login_required
@permission_required("message_broadcast_send")
def personnel_search(request):
    """جستجوی پرسنل برای انتخاب گیرنده (JSON)."""
    from django.http import JsonResponse

    from accounts.models import UserProfile

    if not request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"results": []})

    q = (request.GET.get("q") or "").strip()
    profiles = UserProfile.objects.select_related("user").filter(user__is_active=True)
    if q:
        profiles = profiles.filter(
            Q(personnel_code__icontains=q)
            | Q(national_code__icontains=q)
            | Q(user__first_name__icontains=q)
            | Q(user__last_name__icontains=q)
            | Q(user__username__icontains=q)
        )
    else:
        profiles = profiles.order_by("user__first_name")

    results = [
        {
            "code": p.personnel_code,
            "name": (p.user.get_full_name() or p.user.username) if p.user else "",
            "mobile": p.mobile or "",
        }
        for p in profiles[:100]
        if p.personnel_code
    ]
    return JsonResponse({"results": results})


@login_required
@permission_required("message_broadcast_send")
def template_list(request):
    """مدیریت قالب‌های پیام آماده (ایجاد/حذف/نمایش)."""
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "delete":
            delete_id = request.POST.get("delete_id")
            MessageTemplate.objects.filter(pk=delete_id, created_by=request.user).delete()
            messages.success(request, "قالب پیام حذف شد.")
            return redirect("message_center:template_list")

        # ایجاد قالب جدید
        title = (request.POST.get("title") or "").strip()
        text = (request.POST.get("text") or "").strip()
        channel = request.POST.get("channel") or MessageTemplate.Channel.SMS
        if title and text:
            MessageTemplate.objects.create(
                title=title,
                text=text,
                channel=channel if channel in (MessageTemplate.Channel.SMS, MessageTemplate.Channel.RUBIKA) else MessageTemplate.Channel.SMS,
                created_by=request.user,
            )
            messages.success(request, "قالب پیام ذخیره شد.")
            return redirect("message_center:template_list")
        messages.error(request, "عنوان و متن قالب الزامی است.")

    templates = MessageTemplate.objects.select_related("created_by").order_by("-updated_at")
    context = {
        "templates": templates,
        "channel_choices": MessageTemplate.Channel.choices,
    }
    return render(request, "message_center/template_list.html", context)
