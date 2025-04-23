from django.db import models

SHIFT_CHOICES = [
    ('روزکار اول', 'روزکار اول'),
    ('روزکار دوم', 'روزکار دوم'),
    ('عصرکار اول', 'عصرکار اول'),
    ('عصرکار دوم', 'عصرکار دوم'),
    ('شب کار اول', 'شب کار اول'),
    ('شب کار دوم', 'شب کار دوم'),
    ('OFF اول', 'OFF اول'),
    ('OFF دوم', 'OFF دوم'),
]

GROUP_CHOICES = [
    ('A', 'A'),
    ('B', 'B'),
    ('C', 'C'),
    ('D', 'D'),
]

class InitialShiftSetup(models.Model):
    start_date = models.DateField(verbose_name="تاریخ شروع")  # تاریخ شروع
    group_A_shift = models.CharField(max_length=20, choices=SHIFT_CHOICES, verbose_name="گروه A")  # شیفت اولیه گروه A
    group_B_shift = models.CharField(max_length=20, choices=SHIFT_CHOICES, verbose_name="گروه B")  # شیفت اولیه گروه B
    group_C_shift = models.CharField(max_length=20, choices=SHIFT_CHOICES, verbose_name="گروه C")  # شیفت اولیه گروه C
    group_D_shift = models.CharField(max_length=20, choices=SHIFT_CHOICES, verbose_name="گروه D")  # شیفت اولیه گروه D

    class Meta:
        verbose_name = "تنظیمات اولیه"
        verbose_name_plural = "تنظیمات اولیه شیفت ها"

    def __str__(self):
        return f"Initial setup starting from {self.start_date}"
