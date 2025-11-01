from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import SiteSettings
from .forms import SiteSettingsForm

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

def custom_403_handler(request, exception):
    return render(request, 'core/403.html', status=403)


