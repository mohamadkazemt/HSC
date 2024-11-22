# Generated by Django 5.1.2 on 2024-11-22 18:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_alter_userprofile_mobile'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='code_generated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='verification_code',
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
    ]
