# Generated by Django 5.1.2 on 2024-10-25 17:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('BaseInfo', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='contractor',
            options={'verbose_name': 'پیمانکار', 'verbose_name_plural': 'پیمانکاران'},
        ),
        migrations.AlterModelOptions(
            name='contractorvehicle',
            options={'verbose_name': 'خودرو', 'verbose_name_plural': 'خودروها'},
        ),
        migrations.AlterModelOptions(
            name='miningblock',
            options={'verbose_name': 'بلوک معدنی', 'verbose_name_plural': 'بلوک\u200cهای معدنی'},
        ),
        migrations.AlterModelOptions(
            name='miningmachine',
            options={'verbose_name': 'دستگاه معدنی', 'verbose_name_plural': 'دستگاه های معدنی'},
        ),
        migrations.AddField(
            model_name='miningblock',
            name='type',
            field=models.CharField(choices=[('w', 'باطله'), ('o', 'سنگ پرعیار'), ('T', 'سنگ کم عیار')], default='w', max_length=20, verbose_name='نوع بلوک سنگ'),
        ),
    ]