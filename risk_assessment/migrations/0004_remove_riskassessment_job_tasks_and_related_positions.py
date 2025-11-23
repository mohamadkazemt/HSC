# Generated manually to remove job_tasks and related_positions fields

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('risk_assessment', '0003_alter_riskassessment_people_at_risk'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='riskassessment',
            name='job_tasks',
        ),
        migrations.RemoveField(
            model_name='riskassessment',
            name='related_positions',
        ),
    ]

