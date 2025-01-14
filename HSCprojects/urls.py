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
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from HSCprojects import settings
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

]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)