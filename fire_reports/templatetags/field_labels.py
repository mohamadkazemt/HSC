from django import template

register = template.Library()

STATUS_LABELS = {
    'horn': 'بوق و چراغ گردان',
    'hose': 'شیلنگ‌ها و اتصالات',
    'monitor': 'مانیتور',
    'extinguisher': 'خاموش‌کننده‌های دستی',
    'equipment': 'تجهیزات آتش‌نشانی',
    'foam': 'پودر و فوم',
    'water': 'آب',
    'tire': 'لاستیک‌ها',
    'brake': 'سیستم ترمز',
    'lighting': 'سیستم روشنایی'
}

@register.filter(name='get_field_label')
def get_field_label(field_name):
    """تبدیل نام فیلد انگلیسی به برچسب فارسی"""
    base_name = field_name.replace('_status', '').replace('_description', '')
    return STATUS_LABELS.get(base_name, field_name)