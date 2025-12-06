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
            import core.ai_service as ai_service_module
            ai_service_module._ai_service_instance = None
            
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
    
    # Get multi-provider configuration status
    from django.conf import settings as django_settings
    import os
    
    # Check environment variables directly (for debugging)
    google_keys_env = os.environ.get('GOOGLE_API_KEYS', '')
    groq_key_env = os.environ.get('GROQ_API_KEY', '')
    openrouter_key_env = os.environ.get('OPENROUTER_API_KEY', '')
    
    # Get from Django settings (which should load from .env via decouple)
    google_keys = getattr(django_settings, 'GOOGLE_API_KEYS', [])
    google_keys_count = len(google_keys) if google_keys else 0
    groq_configured = bool(getattr(django_settings, 'GROQ_API_KEY', ''))
    openrouter_configured = bool(getattr(django_settings, 'OPENROUTER_API_KEY', ''))
    google_model = getattr(django_settings, 'GOOGLE_DEFAULT_MODEL', 'gemini-2.0-flash-lite')
    groq_model = getattr(django_settings, 'GROQ_MODEL', 'llama3-70b-8192')
    openrouter_model = getattr(django_settings, 'OPENROUTER_MODEL', 'google/gemini-2.0-flash-lite:free')
    
    # Debug info (for troubleshooting)
    env_debug = {
        'google_keys_from_env': bool(google_keys_env),
        'google_keys_from_settings': google_keys_count,
        'groq_from_env': bool(groq_key_env),
        'groq_from_settings': groq_configured,
        'openrouter_from_env': bool(openrouter_key_env),
        'openrouter_from_settings': openrouter_configured,
        'using_decouple': hasattr(django_settings, 'USE_DECOUPLE') and getattr(django_settings, 'USE_DECOUPLE', False),
    }
    
    context = {
        'form': form,
        'settings': settings,
        'test_info': test_info,
        'google_ai_studio_url': 'https://aistudio.google.com/',
        # Multi-provider status
        'google_keys_count': google_keys_count,
        'groq_configured': groq_configured,
        'openrouter_configured': openrouter_configured,
        'google_model': google_model,
        'groq_model': groq_model,
        'openrouter_model': openrouter_model,
        # Debug info
        'env_debug': env_debug,
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


