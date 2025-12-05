from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import SiteSettings
from .forms import SiteSettingsForm
from .ai_models import AISettings
from .ai_forms import AISettingsForm
from .ai_service import test_ai_connection
import json

@login_required
@user_passes_test(lambda u: u.is_superuser)
def site_settings_view(request):
    settings, created = SiteSettings.objects.get_or_create(pk=1)

    if request.method == 'POST':
        form = SiteSettingsForm(request.POST, request.FILES, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'تنظیمات سایت با موفقیت به‌روزرسانی شد!')
            return redirect('core:site_settings')
    else:
        form = SiteSettingsForm(instance=settings)

    return render(request, 'core/site_settings.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def ai_settings_view(request):
    """صفحه تنظیمات AI"""
    settings = AISettings.get_solo()
    
    if request.method == 'POST':
        form = AISettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            # Reset singleton instance
            from .ai_service import _ai_service_instance
            global _ai_service_instance
            _ai_service_instance = None
            
            messages.success(request, 'تنظیمات AI با موفقیت به‌روزرسانی شد!')
            return redirect('core:ai_settings')
    else:
        form = AISettingsForm(instance=settings)
    
    # نمایش وضعیت آخرین تست
    test_info = None
    if settings.last_tested_at:
        test_info = {
            'tested_at': settings.last_tested_at,
            'status': settings.last_test_status,
            'message': settings.last_test_message,
        }
    
    context = {
        'form': form,
        'settings': settings,
        'test_info': test_info,
        'google_ai_studio_url': 'https://aistudio.google.com/',
    }
    
    return render(request, 'core/ai_settings.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(["POST"])
def ai_test_connection(request):
    """تست اتصال به API AI"""
    try:
        # تست اتصال
        result = test_ai_connection()
        
        # ذخیره نتیجه در دیتابیس
        settings = AISettings.get_solo()
        settings.last_tested_at = timezone.now()
        settings.last_test_status = result.get('success', False)
        settings.last_test_message = result.get('message', '')
        settings.save()
        
        return JsonResponse(result)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"خطا در تست اتصال AI: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'خطا در تست اتصال: {str(e)}',
            'details': None
        }, status=500)

def custom_403_handler(request, exception):
    return render(request, 'core/403.html', status=403)


