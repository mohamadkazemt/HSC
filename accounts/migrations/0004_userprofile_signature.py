# Generated by Django 5.1.2 on 2024-11-25 18:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_userprofile_code_generated_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='signature',
            field=models.ImageField(blank=True, null=True, upload_to='signatures/', verbose_name='امضای کاربر'),
        ),
    ]
