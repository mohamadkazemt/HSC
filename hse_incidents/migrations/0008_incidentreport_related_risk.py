# Generated manually
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hse_incidents', '0007_remove_hsecompletionreport_patient_condition_on_dispatch_and_more'),
        ('risk_assessment', '0005_riskassessment_approval_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='incidentreport',
            name='related_risk',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='related_incidents', to='risk_assessment.riskassessment', verbose_name='ریسک مرتبط'),
        ),
    ]

