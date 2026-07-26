from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('accounts', '0016_userprofile_military_service_status_and_more')]

    operations = [
        migrations.CreateModel(
            name='Dependent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=150, verbose_name='نام')),
                ('last_name', models.CharField(max_length=150, verbose_name='نام خانوادگی')),
                ('father_name', models.CharField(blank=True, max_length=150, verbose_name='نام پدر')),
                ('national_code', models.CharField(max_length=10, verbose_name='کد ملی')),
                ('birth_certificate_number', models.CharField(blank=True, max_length=20, verbose_name='شماره شناسنامه')),
                ('birth_date', models.DateField(blank=True, null=True, verbose_name='تاریخ تولد')),
                ('gender', models.CharField(blank=True, choices=[('male', 'مرد'), ('female', 'زن')], max_length=10, verbose_name='جنسیت')),
                ('mobile', models.CharField(blank=True, max_length=11, verbose_name='شماره تماس')),
                ('relationship', models.CharField(max_length=50, verbose_name='نسبت')),
                ('disease_type', models.CharField(blank=True, max_length=255, verbose_name='نوع بیماری')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('personnel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dependents', to='accounts.userprofile', verbose_name='پرسنل')),
            ],
            options={'verbose_name': 'فرد تحت تکفل', 'verbose_name_plural': 'افراد تحت تکفل', 'ordering': ('last_name', 'first_name')},
        ),
        migrations.AddConstraint(
            model_name='dependent',
            constraint=models.UniqueConstraint(fields=('personnel', 'national_code'), name='unique_dependent_national_code_per_personnel'),
        ),
    ]
