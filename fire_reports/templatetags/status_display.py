from django import template

register = template.Library()

STATUS_LABELS = {
    'horn_status': 'بوق و چراغ گردان',
    'hose_status': 'شیلنگ‌ها و اتصالات',
    'monitor_status': 'مانیتور',
    'extinguisher_status': 'خاموش‌کننده‌های دستی',
    'equipment_status': 'تجهیزات آتش‌نشانی',
    'foam_status': 'پودر و فوم',
    'water_status': 'آب',
    'tire_status': 'لاستیک‌ها',
    'brake_status': 'سیستم ترمز',
    'lighting_status': 'سیستم روشنایی'
}

@register.filter(name='get_field_display')
def get_field_display(field_name):
    """برگرداندن نام نمایشی برای فیلدها"""
    return STATUS_LABELS.get(field_name, field_name)