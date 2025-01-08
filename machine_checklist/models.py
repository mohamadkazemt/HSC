from django.db import models
from django.contrib.auth.models import User
from accounts.models import UserProfile
from BaseInfo.models import MiningMachine, TypeMachine
from shift_manager.utils import get_current_shift_and_group, get_current_shift_and_group_without_user


class Checklist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='کاربر', null=True, blank=True)
    machine = models.ForeignKey(MiningMachine, on_delete=models.CASCADE, verbose_name='ماشین')
    date = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ و زمان ایجاد')
    shift = models.CharField(max_length=20, blank=True, null=True, verbose_name='شیفت کاری')
    shift_group = models.CharField(max_length=2, blank=True, null=True, verbose_name='گروه شیفت')

    def save(self, *args, **kwargs):
        if self.user and self.user.is_authenticated:
             current_shift, current_group = get_current_shift_and_group(self.user)
             if hasattr(self.user, 'userprofile'):
                self.shift_group = self.user.userprofile.group
             else:
                 self.shift_group = current_group
        else:
            current_shift, current_group = get_current_shift_and_group_without_user()
            self.shift_group = current_group

        self.shift = current_shift
        super(Checklist, self).save(*args, **kwargs)

    def __str__(self):
        return f"چک لیست {self.machine.machine_type.name} - {self.date}"

    class Meta:
        verbose_name = "چک لیست"
        verbose_name_plural = "چک لیست ها"


class Question(models.Model):
    machine_type = models.ForeignKey(TypeMachine, on_delete=models.CASCADE, verbose_name='نوع دستگاه')
    text = models.TextField(verbose_name='متن سوال')
    is_required = models.BooleanField(default=True, verbose_name='اجباری')
    question_type = models.CharField(max_length=20, choices=[('text', 'متنی'), ('option', 'گزینه ای')], default='text',
                                     verbose_name='نوع سوال')
    options = models.TextField(blank=True, null=True, verbose_name='گزینه ها (با کاما جدا شود)')

    def __str__(self):
        return f"{self.text} ({self.machine_type.name})"

    class Meta:
        verbose_name = "سوال"
        verbose_name_plural = "سوالات"


class Answer(models.Model):
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, verbose_name='چک لیست')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name='سوال')
    answer_text = models.TextField(blank=True, null=True, verbose_name='پاسخ متنی')
    selected_option = models.CharField(max_length=255, blank=True, null=True, verbose_name='گزینه انتخاب شده')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات اضافی')

    def __str__(self):
        return f"پاسخ به {self.question.text}"

    class Meta:
        verbose_name = "پاسخ"
        verbose_name_plural = "پاسخ ها"