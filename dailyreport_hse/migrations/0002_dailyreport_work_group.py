# Generated by Django 5.1.2 on 2024-12-18 04:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dailyreport_hse', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailyreport',
            name='work_group',
            field=models.CharField(choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], default='A', max_length=1, verbose_name='گروه کاری'),
            preserve_default=False,
        ),
    ]
