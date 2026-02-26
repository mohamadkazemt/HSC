from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('mining_operations', '0003_dumpcountsession_dumpcountevent'),
    ]

    operations = [
        migrations.AddField(
            model_name='loadinghaulingreport',
            name='loader_operator_name',
            field=models.CharField(blank=True, max_length=150, verbose_name='نام بارکننده'),
        ),
    ]
