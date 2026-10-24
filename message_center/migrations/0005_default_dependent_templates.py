from django.db import migrations


def create_default_templates(apps, schema_editor):
    MessageTemplate = apps.get_model('message_center', 'MessageTemplate')

    templates = [
        {
            'title': 'فراخوان تکمیل اطلاعات افراد تحت تکفل (SMS)',
            'channel': 'sms',
            'text': (
                'همکار گرامی،\n'
                'جهت تکمیل و به‌روزرسانی اطلاعات افراد تحت تکفل خود، لطفاً به سامانه زیر مراجعه نمایید:\n'
                'https://miepcoj.ir/d/\n'
                'ورود با کد پرسنلی و رمز یکبارمصرف پیامکی\n'
                'امور اداری و منابع انسانی'
            ),
        },
        {
            'title': 'فراخوان تکمیل اطلاعات افراد تحت تکفل (روبیکا)',
            'channel': 'rubika',
            'text': (
                'همکار گرامی،\n'
                'جهت تکمیل و به‌روزرسانی اطلاعات افراد تحت تکفل خود، لطفاً به سامانه زیر مراجعه نمایید:\n'
                'https://miepcoj.ir/d/\n'
                'ورود با کد پرسنلی و رمز یکبارمصرف پیامکی\n'
                'امور اداری و منابع انسانی'
            ),
        },
    ]

    for item in templates:
        MessageTemplate.objects.get_or_create(
            title=item['title'],
            defaults={'channel': item['channel'], 'text': item['text'], 'is_active': True},
        )


def remove_default_templates(apps, schema_editor):
    MessageTemplate = apps.get_model('message_center', 'MessageTemplate')
    MessageTemplate.objects.filter(
        title__in=[
            'فراخوان تکمیل اطلاعات افراد تحت تکفل (SMS)',
            'فراخوان تکمیل اطلاعات افراد تحت تکفل (روبیکا)',
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('message_center', '0004_alter_reminderlog_status'),
    ]

    operations = [
        migrations.RunPython(create_default_templates, remove_default_templates),
    ]
