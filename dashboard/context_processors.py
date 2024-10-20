# dashboard/context_processors.py

def notification_context_processor(request):
    if request.user.is_authenticated:
        unread_notifications = request.user.notifications.filter(is_read=False)
        read_notifications = request.user.notifications.filter(is_read=True)
        unread_notifications_count = unread_notifications.count()
        return {
            'unread_notifications': unread_notifications,
            'read_notifications': read_notifications,
            'unread_notifications_count': unread_notifications_count
        }
    return {}
