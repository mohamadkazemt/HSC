from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rubika_bot', '0008_webhooklog'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rubikabotsettings',
            name='base_api_url',
        ),
        migrations.RemoveField(
            model_name='rubikabotsettings',
            name='deeplink_template',
        ),
        migrations.AlterField(
            model_name='rubikabotsettings',
            name='token',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddIndex(
            model_name='rubikauser',
            index=models.Index(fields=['first_name'], name='rubika_user_fn_idx'),
        ),
        migrations.AddIndex(
            model_name='rubikauser',
            index=models.Index(fields=['last_name'], name='rubika_user_ln_idx'),
        ),
    ]

