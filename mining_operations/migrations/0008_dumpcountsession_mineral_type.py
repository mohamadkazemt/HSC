from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('BaseInfo', '0008_mineraltype_dump'),
        ('mining_operations', '0007_remove_dumpcount_event_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='dumpcountsession',
            name='mineral_type',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='dump_count_sessions',
                to='BaseInfo.mineraltype',
                verbose_name='نوع ماده معدنی',
            ),
        ),
    ]
