"""
Middleware برای محدود کردن دسترسی پرسنل اورژانس (پرستار و پزشک) به بخش‌های غیر اورژانس
"""
from django.shortcuts import redirect
from django.contrib import messages


class EmergencyPersonnelAccessMiddleware:
    """
    این middleware دسترسی پرسنل اورژانس (EmergencyNurse و EmergencyDoctor) را 
    به بخش‌های غیر اورژانس محدود می‌کند.
    مدیر اورژانس (EmergencyManager) و سوپریوزرها از این محدودیت مستثنی هستند.
    """
    
    # مسیرهای استثنا که همیشه مجاز هستند (برای همه کاربران)
    EXEMPT_PATHS = [
        '/admin/',
        '/static/',
        '/media/',
        '/select2/',
        '/c/',  # لینک‌های کوتاه
        '/accounts/logout/',  # خروج از سیستم
        '/admin/logout/',  # خروج از ادمین
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # بررسی اینکه آیا کاربر لاگین کرده است
        if request.user.is_authenticated:
            # بررسی اینکه آیا کاربر پرسنل اورژانس است (نه مدیر)
            is_emergency_nurse = request.user.groups.filter(name='EmergencyNurse').exists()
            is_emergency_doctor = request.user.groups.filter(name='EmergencyDoctor').exists()
            is_emergency_manager = request.user.groups.filter(name='EmergencyManager').exists()
            
            # اگر کاربر پرستار یا پزشک است (نه مدیر) و سوپریوزر هم نیست
            if (is_emergency_nurse or is_emergency_doctor) and not is_emergency_manager and not request.user.is_superuser:
                path = request.path
                
                # بررسی مسیرهای استثنا
                if any(path.startswith(exempt) for exempt in self.EXEMPT_PATHS):
                    return self.get_response(request)
                
                # اگر مسیر emergency نیست، redirect به emergency dashboard
                if not path.startswith('/emergency/'):
                    messages.warning(request, 'شما فقط به بخش اورژانس دسترسی دارید.')
                    return redirect('emergency_services:dashboard')
        
        response = self.get_response(request)
        return response

