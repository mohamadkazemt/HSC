import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HSCprojects.settings')
django.setup()

from hse_incidents.models import IncidentType

# حذف انواع حادثه قدیمی اگر وجود داشت
IncidentType.objects.all().delete()

# افزودن انواع حادثه انسانی (فردی)
human_incidents = [
    IncidentType(category='human', name='بریدگی', description='حادثه ناشی از بریدگی اشخاص'),
    IncidentType(category='human', name='سوختگی', description='حادثه ناشی از سوختگی اشخاص'),
    IncidentType(category='human', name='آسیب چشم', description='حادثه ناشی از آسیب چشم'),
    IncidentType(category='human', name='شکستگی استخوان', description='حادثه ناشی از شکستگی استخوان'),
    IncidentType(category='human', name='سقوط از ارتفاع', description='حادثه ناشی از سقوط از ارتفاع'),
    IncidentType(category='human', name='ضربه به بدن', description='حادثه ناشی از ضربه به بدن'),
    IncidentType(category='human', name='آسیب بدون شناخت واضح', description='سایر آسیب‌های انسانی'),
]

# افزودن انواع حادثه تجهیزاتی
equipment_incidents = [
    IncidentType(category='equipment', name='خرابی ماشین', description='خرابی یا آسیب به ماشین‌آلات'),
    IncidentType(category='equipment', name='نشت سیال', description='نشت روغن، آب یا سیالات دیگر'),
    IncidentType(category='equipment', name='آتش‌سوزی تجهیزات', description='حریق یا آتش‌سوزی در تجهیزات'),
    IncidentType(category='equipment', name='شکست تجهیزات', description='شکستگی یا پاره شدن اجزاء'),
    IncidentType(category='equipment', name='انفجار', description='انفجار در تجهیزات یا لوله‌ها'),
    IncidentType(category='equipment', name='بیش‌فشار سیستم', description='بیش‌فشار یا بیش‌ولتاژ در سیستم'),
    IncidentType(category='equipment', name='عطل الکتریکی', description='آتش‌سوزی یا عطل الکتریکی'),
]

# افزودن انواع حادثه محیط زیستی
environmental_incidents = [
    IncidentType(category='environmental', name='آلودگی آب', description='آلودگی آب‌های سطحی یا زیرزمینی'),
    IncidentType(category='environmental', name='آلودگی خاک', description='آلودگی خاک به مواد شیمیایی'),
    IncidentType(category='environmental', name='آلودگی هوا', description='انتشار گاز یا آلودگی هوا'),
    IncidentType(category='environmental', name='نشت مواد خطرناک', description='نشت مواد شیمیایی خطرناک'),
    IncidentType(category='environmental', name='مسائل نویز و لرزش', description='صدای بلند یا لرزش‌های غیرمتناسب'),
    IncidentType(category='environmental', name='آسیب به گیاهان و جانوران', description='تأثیر منفی بر محیط زیست'),
]

# ذخیره تمام انواع حادثه
all_incidents = human_incidents + equipment_incidents + environmental_incidents
for incident in all_incidents:
    incident.save()
    print(f"✓ {incident.get_category_display()}: {incident.name}")

print(f"\n✓ کل {len(all_incidents)} نوع حادثه با موفقیت اضافه شد!")
