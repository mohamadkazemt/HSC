from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils import timezone

from BaseInfo.models import MineralType, MiningMachine, MiningBlock, Dump


class ShiftChoices(models.TextChoices):
    A = 'A', 'A'
    B = 'B', 'B'
    C = 'C', 'C'
    D = 'D', 'D'


class StopReasonChoices(models.TextChoices):
    BREAKDOWN = 'breakdown', 'خرابی'
    SERVICE = 'service', 'سرویس'
    NOT_READY = 'not_ready', 'بی آمادگی'
    WEATHER = 'weather', 'جوی'
    LOADER_BREAKDOWN = 'loader_breakdown', 'خرابی بارکننده'


class MachineActivity(models.Model):
    machine = models.ForeignKey(
        MiningMachine,
        on_delete=models.CASCADE,
        related_name='machine_activities',
        verbose_name='ماشین',
    )
    date = models.DateField(verbose_name='تاریخ')
    shift = models.CharField(max_length=1, choices=ShiftChoices.choices, verbose_name='شیفت')
    operator_name = models.CharField(max_length=150, verbose_name='نام اپراتور')

    start_hour = models.TimeField(null=True, blank=True, verbose_name='ساعت شروع')
    end_hour = models.TimeField(null=True, blank=True, verbose_name='ساعت پایان')

    ready_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='ساعات آماده به کاری',
    )
    work_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='ساعات کارکرد',
    )
    stop_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='ساعات توقف',
    )
    stop_reason = models.CharField(
        max_length=20,
        choices=StopReasonChoices.choices,
        null=True,
        blank=True,
        verbose_name='علت توقف',
    )
    stop_description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='شرح علت توقف',
    )

    breakdown_alert_sent = models.BooleanField(default=False, verbose_name='هشدار خرابی ارسال شده')

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_machine_activities',
        verbose_name='ایجاد کننده',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'فعالیت ماشین'
        verbose_name_plural = 'فعالیت ماشین ها'
        ordering = ['-date', 'shift', 'machine__workshop_code']
        indexes = [
            models.Index(fields=['date', 'shift']),
            models.Index(fields=['machine', 'date']),
        ]

    def __str__(self):
        return f'{self.machine.workshop_code} - {self.date} - {self.shift}'

    def clean(self):
        total = (self.ready_hours or Decimal('0')) + (self.work_hours or Decimal('0')) + (self.stop_hours or Decimal('0'))
        if total > Decimal('24'):
            raise ValidationError('مجموع ساعات آماده به کاری، کارکرد و توقف نباید بیشتر از 24 باشد.')

        if (self.stop_hours or Decimal('0')) > 0 and not (self.stop_reason or self.stop_description):
            raise ValidationError({'stop_reason': 'برای ثبت توقف، تعیین علت توقف الزامی است.'})

    def save(self, *args, **kwargs):
        self.full_clean()

        should_notify = (
            self.stop_reason == StopReasonChoices.BREAKDOWN
            and (self.stop_hours or Decimal('0')) > Decimal('2')
            and not self.breakdown_alert_sent
        )

        super().save(*args, **kwargs)

        if should_notify:
            self._notify_breakdown_over_two_hours()
            MachineActivity.objects.filter(pk=self.pk).update(breakdown_alert_sent=True)
            self.breakdown_alert_sent = True

    @classmethod
    def calculate_shift_totals(cls, report_date, shift):
        totals = cls.objects.filter(date=report_date, shift=shift).aggregate(
            total_work_hours=Sum('work_hours'),
            total_ready_hours=Sum('ready_hours'),
            total_stop_hours=Sum('stop_hours'),
        )
        return {
            'total_work_hours': totals['total_work_hours'] or Decimal('0'),
            'total_ready_hours': totals['total_ready_hours'] or Decimal('0'),
            'total_stop_hours': totals['total_stop_hours'] or Decimal('0'),
        }

    def _notify_breakdown_over_two_hours(self):
        from rubika_bot.tasks import send_rubika_message

        User = get_user_model()
        admins = (
            User.objects
            .filter(is_superuser=True, is_active=True, rubika_profile__isnull=False)
            .exclude(rubika_profile__chat_id='')
            .select_related('rubika_profile')
        )

        message = (
            'هشدار توقف ماشین\n'
            f'ماشین: {self.machine.workshop_code}\n'
            f'تاریخ: {self.date}\n'
            f'شیفت: {self.shift}\n'
            f'اپراتور: {self.operator_name}\n'
            f'مدت خرابی: {self.stop_hours} ساعت'
        )

        for admin in admins:
            try:
                send_rubika_message.delay(admin.rubika_profile.chat_id, message)
            except Exception:
                try:
                    send_rubika_message(admin.rubika_profile.chat_id, message)
                except Exception:
                    pass


class LoadingHaulingReport(models.Model):
    loader_machine = models.ForeignKey(
        MiningMachine,
        on_delete=models.CASCADE,
        related_name='loader_reports',
        verbose_name='ماشین بارکننده',
    )
    loader_operator_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='نام بارکننده',
    )
    dumper_machine = models.ForeignKey(
        MiningMachine,
        on_delete=models.CASCADE,
        related_name='dumper_reports',
        verbose_name='ماشین حمل کننده',
    )
    dumper_operator_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='نام راننده دامپ',
    )
    shift = models.CharField(max_length=1, choices=ShiftChoices.choices, verbose_name='شیفت')
    material_type = models.ForeignKey(
        MineralType,
        on_delete=models.PROTECT,
        related_name='loading_hauling_reports',
        verbose_name='نوع ماده معدنی',
    )
    block = models.ForeignKey(
        MiningBlock,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='loading_hauling_reports',
        verbose_name='شماره بلوک',
    )
    dump = models.ForeignKey(
        Dump,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='loading_hauling_reports',
        verbose_name='محل تخلیه (دامپ)',
    )
    service_count = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name='تعداد سرویس')
    date = models.DateField(verbose_name='تاریخ')

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_loading_hauling_reports',
        verbose_name='ایجاد کننده',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'گزارش بارکننده و حمل کننده'
        verbose_name_plural = 'گزارش های بارکننده و حمل کننده'
        ordering = ['-date', 'shift', 'loader_machine__workshop_code']
        indexes = [
            models.Index(fields=['date', 'shift']),
            models.Index(fields=['loader_machine', 'dumper_machine']),
        ]

    def __str__(self):
        return f'{self.date} - {self.shift} - {self.loader_machine.workshop_code}/{self.dumper_machine.workshop_code}'

    def clean(self):
        if self.loader_machine_id and self.dumper_machine_id and self.loader_machine_id == self.dumper_machine_id:
            raise ValidationError('ماشین بارکننده و حمل کننده نمی توانند یکسان باشند.')


def current_local_time():
    return timezone.localtime().time().replace(microsecond=0)


class DumpCountSession(models.Model):
    date = models.DateField(verbose_name='تاریخ')
    shift = models.CharField(max_length=1, choices=ShiftChoices.choices, verbose_name='شیفت')
    mineral_type = models.ForeignKey(
        MineralType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dump_count_sessions',
        verbose_name='نوع ماده معدنی',
    )
    block = models.ForeignKey(
        MiningBlock,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dump_count_sessions',
        verbose_name='شماره بلوک',
    )
    dump = models.ForeignKey(
        Dump,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dump_count_sessions',
        verbose_name='محل تخلیه (دامپ)',
    )
    loader_machine = models.ForeignKey(
        MiningMachine,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dump_count_sessions_as_loader',
        verbose_name='ماشین بارکننده',
    )
    counter_name = models.CharField(max_length=150, verbose_name='نام کنترچی')
    loader_operator_name = models.CharField(max_length=150, blank=True, verbose_name='نام راننده/بارکننده')
    start_time = models.TimeField(default=current_local_time, verbose_name='ساعت شروع شیفت')
    end_time = models.TimeField(null=True, blank=True, verbose_name='ساعت پایان شیفت')
    notes = models.CharField(max_length=255, blank=True, verbose_name='توضیحات')

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_dump_count_sessions',
        verbose_name='ایجاد کننده',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')

    class Meta:
        verbose_name = 'شیفت شمارش دامپ'
        verbose_name_plural = 'شیفت های شمارش دامپ'
        ordering = ['-date', '-created_at']
        indexes = [models.Index(fields=['date', 'shift'])]

    def __str__(self):
        block_label = self.block.block_name if self.block else '-'
        return f'{self.date} - شیفت {self.shift} - بلوک {block_label}'

    @property
    def total_loads(self):
        return self.dump_events.count()


class DumpCountEvent(models.Model):
    session = models.ForeignKey(
        DumpCountSession,
        on_delete=models.CASCADE,
        related_name='dump_events',
        verbose_name='شیفت شمارش',
    )
    dumper_machine = models.ForeignKey(
        MiningMachine,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='counted_dumps',
        verbose_name='دامپتراک',
    )
    driver_name = models.CharField(max_length=150, blank=True, verbose_name='نام راننده')
    load_time = models.DateTimeField(default=timezone.now, verbose_name='زمان ثبت سرویس')
    note = models.CharField(max_length=255, blank=True, verbose_name='توضیحات')

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_dump_count_events',
        verbose_name='ثبت کننده',
    )

    class Meta:
        verbose_name = 'رکورد شمارش دامپ'
        verbose_name_plural = 'رکوردهای شمارش دامپ'
        ordering = ['-load_time']
        indexes = [models.Index(fields=['session', 'load_time'])]

    def __str__(self):
        return f'{self.session} - {self.load_time}'
