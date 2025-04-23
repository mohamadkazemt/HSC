from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from .utils import log_user_activity


@receiver(user_logged_in)
def user_logged_in_callback(sender, request, user, **kwargs):
    log_user_activity(
        user=user,
        activity_type='login',
        description='ورود به سیستم',
        request=request
    )


@receiver(user_logged_out)
def user_logged_out_callback(sender, request, user, **kwargs):
    if user:  # در برخی موارد ممکن است user None باشد
        log_user_activity(
            user=user,
            activity_type='logout',
            description='خروج از سیستم',
            request=request
        ) 