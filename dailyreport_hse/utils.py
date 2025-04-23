# Utility function to get or create DailyReport
from django.utils.timezone import now
from .models import (
    DailyReport,
    BlastingDetail,
    DrillingDetail,
    DumpDetail,
    LoadingDetail,
    InspectionDetail,
    StoppageDetail,
    FollowupDetail
)


def get_or_create_daily_report(user):
    report, created = DailyReport.objects.get_or_create(
        user=user,
        created_at__date=now().date(),
        defaults={
            "is_complete": False,
        }
    )
    return report