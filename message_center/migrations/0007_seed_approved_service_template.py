from django.db import migrations


def seed_service_template(apps, schema_editor):
    MessageTemplate = apps.get_model('message_center', 'MessageTemplate')
    SMSTemplate = apps.get_model('dashboard', 'SMSTemplate')

    # ۱. ثبت در قالب‌های مرکز پیام
    MessageTemplate.objects.get_or_create(
        title='اطلاع‌رسانی پرسنلی (قالب خدماتی ۲۵۳۰۸۵)',
        defaults={
            'channel': 'sms',
            'text': (
                'همکار گرامی #NAME#\n'
                'موضوع: #TITLE#\n'
                'شرح: #TEXT#\n'
                'سامانه MIEPCO: #LINK#\n'
                'شرکت کاراوران صنعت خاورمیانه'
            ),
            'is_active': True,
        },
    )

    # ۲. ثبت در قالب‌های مرکزی SMS.ir
    SMSTemplate.objects.update_or_create(
        template_id=253085,
        defaults={
            'name': 'اطلاع‌رسانی پرسنلی (کاراوران)',
            'description': 'قالب خدماتی مصوب ۲۵۳۰۸۵ جهت عبور ۱۰۰٪ از بلک‌لیست مخابرات',
            'template_text': (
                'همکار گرامی {NAME}\n'
                'موضوع: {TITLE}\n'
                'شرح: {TEXT}\n'
                'سامانه MIEPCO: {LINK}\n'
                'شرکت کاراوران صنعت خاورمیانه'
            ),
            'parameters': ['NAME', 'TITLE', 'TEXT', 'LINK'],
            'is_active': True,
        },
    )


def rollback_service_template(apps, schema_editor):
    MessageTemplate = apps.get_model('message_center', 'MessageTemplate')
    SMSTemplate = apps.get_model('dashboard', 'SMSTemplate')

    MessageTemplate.objects.filter(title='اطلاع‌رسانی پرسنلی (قالب خدماتی ۲۵۳۰۸۵)').delete()
    SMSTemplate.objects.filter(template_id=253085).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('message_center', '0006_broadcast_sms_pack_id_and_more'),
        ('dashboard', '0006_smstemplate_smslog_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_service_template, rollback_service_template),
    ]
