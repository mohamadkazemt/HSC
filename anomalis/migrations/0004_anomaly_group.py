# Generated by Django 5.1.1 on 2024-10-12 17:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('anomalis', '0003_alter_anomaly_created_by_alter_anomaly_followup'),
    ]

    operations = [
        migrations.AddField(
            model_name='anomaly',
            name='group',
            field=models.CharField(choices=[('A', 'گروه A'), ('B', 'گروه B'), ('C', 'گروه C'), ('D', 'گروه D'), ('G', 'گروه G')], default=1, max_length=1, verbose_name='گروه کاری'),
            preserve_default=False,
        ),
    ]
