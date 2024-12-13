# Generated by Django 5.1.2 on 2024-12-13 06:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dailyreport_hse', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='followupdetail',
            name='files',
            field=models.FileField(blank=True, null=True, upload_to='followups/', verbose_name='فایل\u200cها'),
        ),
        migrations.AlterField(
            model_name='blastingdetail',
            name='status',
            field=models.BooleanField(default=False, verbose_name='وضعیت آتشباری'),
        ),
    ]
