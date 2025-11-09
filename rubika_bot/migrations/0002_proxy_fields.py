from django.db import migrations, models
import django_cryptography.fields


class Migration(migrations.Migration):

    dependencies = [
        ('rubika_bot', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='rubikabotsettings',
            name='proxy_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='rubikabotsettings',
            name='proxy_host',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='rubikabotsettings',
            name='proxy_password',
            field=django_cryptography.fields.encrypt(models.CharField(blank=True, max_length=255, null=True)),
        ),
        migrations.AddField(
            model_name='rubikabotsettings',
            name='proxy_port',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='rubikabotsettings',
            name='proxy_scheme',
            field=models.CharField(choices=[('socks5', 'SOCKS5'), ('http', 'HTTP'), ('https', 'HTTPS')], default='socks5', max_length=10),
        ),
        migrations.AddField(
            model_name='rubikabotsettings',
            name='proxy_username',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]

