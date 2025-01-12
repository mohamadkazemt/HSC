
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Report
from .utils import get_current_user_shift_and_group  # ایمپورت تابع جدید

@receiver(pre_save, sender=Report)
def set_shift_and_group(sender, instance, **kwargs):
    # دریافت شیفت و گروه جاری از تابع جدید
    current_shift, current_group = get_current_user_shift_and_group(instance.user)
    if current_shift and current_group:
        instance.shift = current_shift
        instance.group = current_group
    else:
       instance.shift = None
       instance.group = None