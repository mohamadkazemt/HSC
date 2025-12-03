"""
Migration برای اضافه کردن مدل ExpiredMedicineLog
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('emergency_services', '0004_medicine_drug_type_medicine_total_unit_volume_and_more'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExpiredMedicineLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('medicine_name', models.CharField(max_length=200, verbose_name='نام دارو')),
                ('medicine_category', models.CharField(blank=True, max_length=100, verbose_name='دسته‌بندی')),
                ('quantity', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='موجودی هنگام انقضا')),
                ('expiry_date', models.DateField(verbose_name='تاریخ انقضا')),
                ('detected_date', models.DateField(auto_now_add=True, verbose_name='تاریخ تشخیص منقضی')),
                ('disposal_date', models.DateField(blank=True, null=True, verbose_name='تاریخ حذف/دفع')),
                ('disposal_method', models.CharField(
                    choices=[
                        ('deleted', 'حذف از سیستم'),
                        ('incinerated', 'سوزانده شده'),
                        ('donated', 'اهدا شده'),
                        ('returned', 'برگشت به تولیدکننده'),
                        ('other', 'سایر')
                    ],
                    default='deleted',
                    max_length=50,
                    verbose_name='روش دفع'
                )),
                ('notes', models.TextField(blank=True, null=True, verbose_name='یادداشت‌ها')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاریخ آخرین بروزرسانی')),
                ('disposal_by_user', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='medicine_disposals',
                    to='auth.user',
                    verbose_name='حذف شده توسط'
                )),
            ],
            options={
                'verbose_name': 'گزارش دارو منقضی',
                'verbose_name_plural': 'گزارش‌های داروهای منقضی',
                'ordering': ['-disposal_date', '-detected_date'],
            },
        ),
        migrations.AddIndex(
            model_name='expiredmedicinelog',
            index=models.Index(fields=['-disposal_date'], name='emergency_s_disposal_idx'),
        ),
        migrations.AddIndex(
            model_name='expiredmedicinelog',
            index=models.Index(fields=['-detected_date'], name='emergency_s_detected_idx'),
        ),
    ]
