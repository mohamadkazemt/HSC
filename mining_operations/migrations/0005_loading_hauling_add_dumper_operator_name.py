from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('mining_operations', '0004_loading_hauling_add_loader_operator_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='loadinghaulingreport',
            name='dumper_operator_name',
            field=models.CharField(blank=True, max_length=150, verbose_name='نام راننده دامپ'),
        ),
    ]
