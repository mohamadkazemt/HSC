from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leave_reports', '0008_shiftreport_exported_to_excel'),
    ]

    operations = [
        migrations.AddField(
            model_name='shiftreport',
            name='registration',
            field=models.BooleanField(choices=[(True, 'ثبت شده'), (False, 'ثبت نشده')], default=False, verbose_name='وضعیت ثبت'),
        ),
    ]
