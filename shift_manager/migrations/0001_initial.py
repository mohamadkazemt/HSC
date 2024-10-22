# Generated by Django 5.1.2 on 2024-10-22 10:45

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='InitialShiftSetup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField(verbose_name='تاریخ شروع')),
                ('group_A_shift', models.CharField(choices=[('روزکار اول', 'روزکار اول'), ('روزکار دوم', 'روزکار دوم'), ('عصرکار اول', 'عصرکار اول'), ('عصرکار دوم', 'عصرکار دوم'), ('شب کار اول', 'شب کار اول'), ('شب کار دوم', 'شب کار دوم'), ('OFF اول', 'OFF اول'), ('OFF دوم', 'OFF دوم')], max_length=20, verbose_name='گروه A')),
                ('group_B_shift', models.CharField(choices=[('روزکار اول', 'روزکار اول'), ('روزکار دوم', 'روزکار دوم'), ('عصرکار اول', 'عصرکار اول'), ('عصرکار دوم', 'عصرکار دوم'), ('شب کار اول', 'شب کار اول'), ('شب کار دوم', 'شب کار دوم'), ('OFF اول', 'OFF اول'), ('OFF دوم', 'OFF دوم')], max_length=20, verbose_name='گروه B')),
                ('group_C_shift', models.CharField(choices=[('روزکار اول', 'روزکار اول'), ('روزکار دوم', 'روزکار دوم'), ('عصرکار اول', 'عصرکار اول'), ('عصرکار دوم', 'عصرکار دوم'), ('شب کار اول', 'شب کار اول'), ('شب کار دوم', 'شب کار دوم'), ('OFF اول', 'OFF اول'), ('OFF دوم', 'OFF دوم')], max_length=20, verbose_name='گروه C')),
                ('group_D_shift', models.CharField(choices=[('روزکار اول', 'روزکار اول'), ('روزکار دوم', 'روزکار دوم'), ('عصرکار اول', 'عصرکار اول'), ('عصرکار دوم', 'عصرکار دوم'), ('شب کار اول', 'شب کار اول'), ('شب کار دوم', 'شب کار دوم'), ('OFF اول', 'OFF اول'), ('OFF دوم', 'OFF دوم')], max_length=20, verbose_name='گروه D')),
            ],
            options={
                'verbose_name': 'تنظیمات اولیه',
                'verbose_name_plural': 'تنظیمات اولیه شیفت ها',
            },
        ),
    ]
