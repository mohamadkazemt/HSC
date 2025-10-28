"""
URL configuration for HSCprojects project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from django.templatetags.static import static as static_url
from HSCprojects import settings as project_settings
from core import views  # وارد کردن views از اپلیکیشن core

handler403 = views.custom_403_handler  # استفاده از هندلر از core

urlpatterns = [
    path('', include('accounts.urls', namespace='accounts_root')),
    path('accounts/', include('accounts.urls', namespace='accounts')),

    path('admin/', admin.site.urls),
    path('dashboard/', include('dashboard.urls')),
    path('anomalis/', include('anomalis.urls')),
    path('select2/', include('django_select2.urls')),
    path('OperationsShiftReports/', include('OperationsShiftReports.urls')),
    path('leave_reports/', include('leave_reports.urls')),
    path('dailyreport_hse/', include('dailyreport_hse.urls')),
    path("permissions/", include("permissions.urls")),
    path("contractor/", include("contractor_management.urls")),
    path('hse_incidents/', include(('hse_incidents.urls', 'hse_incidents'), namespace='hse_incidents')),
    path('machine-checklist/', include(('machine_checklist.urls', 'machine_checklist'), namespace='machine_checklist')),
    path('shift-manager/', include('shift_manager.urls')),
    path('fire-reports/', include(('fire_reports.urls', 'fire_reports'), namespace='fire_reports')),
    path('meetings/', include('meetings.urls')),
    path('checklist_app/', include('checklist_app.urls')),
    path('emergency/', include('emergency_services.urls', namespace='emergency_services')),
    path('fire_extinguisher_management/', include('fire_extinguisher_management.urls', namespace='fire_extinguisher_management')),
    path('core/', include('core.urls', namespace='core')),
]

# اضافه کردن مسیرهای media و static در حالت debug
if getattr(settings, 'DEBUG', False):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # اضافه کردن مسیرهای Django Debug Toolbar
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]

# favicon redirect
urlpatterns += [
    path('favicon.ico', RedirectView.as_view(url=static_url('assets/media/logos/favicon.ico'), permanent=True)),
]
