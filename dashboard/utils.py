from .models import UserActivity


def log_user_activity(user, activity_type, description, related_model=None, related_object_id=None, url=None, request=None):
    """
    ثبت فعالیت کاربر در سیستم
    
    پارامترها:
    - user: کاربر انجام دهنده فعالیت
    - activity_type: نوع فعالیت (login, logout, create, update, delete, view, other)
    - description: توضیح فعالیت
    - related_model: نام مدل مرتبط (اختیاری)
    - related_object_id: شناسه شیء مرتبط (اختیاری)
    - url: آدرس URL مرتبط با فعالیت (اختیاری)
    - request: شیء درخواست HTTP (اختیاری، برای دریافت IP)
    """
    ip_address = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
    
    UserActivity.objects.create(
        user=user,
        activity_type=activity_type,
        description=description,
        related_model=related_model,
        related_object_id=related_object_id,
        url=url,
        ip_address=ip_address
    ) 