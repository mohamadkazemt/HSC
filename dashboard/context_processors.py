from .models import Notification


def notification_context_processor(request):
    if request.user.is_authenticated:
        unread_notifications_count = request.user.notifications.filter(is_read=False).count()
        return {'unread_notifications_count': unread_notifications_count}
    return {}


# dashboard/context_processors.py



def notifications(request):
    if request.user.is_authenticated:
        unread_notifications_count = request.user.notifications.filter(is_read=False).count()
        return {'unread_notifications_count': unread_notifications_count}
    return {}
