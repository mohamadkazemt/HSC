# Generated by Django 5.1.2 on 2025-01-05 15:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hse_incidents', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='InjuryType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='نوع جراحت')),
            ],
        ),
        migrations.RemoveField(
            model_name='incidentreport',
            name='injury_type',
        ),
        migrations.AddField(
            model_name='incidentreport',
            name='injury_type',
            field=models.ManyToManyField(blank=True, related_name='incident_reports', to='hse_incidents.injurytype', verbose_name='نوع جراحت'),
        ),
    ]
