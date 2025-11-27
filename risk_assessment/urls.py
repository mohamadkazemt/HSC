from django.urls import path
from . import views

app_name = 'risk_assessment'

urlpatterns = [
    # داشبورد اصلی
    path('dashboard/', views.risk_dashboard, name='risk_dashboard'),
    # لیست جامع ریسک‌ها
    path('list/', views.risk_global_list, name='risk_list'),
    
    # صفحه شروع (انتخاب شغل برای ثبت ریسک)
    path('create/', views.risk_create_start, name='risk_create'),
    # alias برای سازگاری با قالب هایی که از نام قبلی استفاده می کنند
    path('create/', views.risk_create_start, name='risk_create_start'),
    
    # لیست ریسک‌های یک شغل
    path('position/<int:position_id>/', views.position_risk_list, name='position_risks'),
    
    # افزودن ریسک جدید برای شغل خاص
    path('position/<int:position_id>/add/', views.risk_create_for_position, name='risk_create_for_position'),
    
    # ویرایش ریسک
    path('risk/<int:risk_id>/edit/', views.risk_update, name='risk_update'),
    
    # جزئیات ریسک
    path('risk/<int:risk_id>/', views.risk_detail, name='risk_detail'),
    
    # ارزیابی مجدد
    path('risk/<int:risk_id>/re-evaluate/', views.risk_re_evaluate, name='risk_re_evaluate'),
    
    # حذف ریسک
    path('risk/<int:risk_id>/delete/', views.risk_delete, name='risk_delete'),
    
    # نمایش ماتریس کلی
    path('matrix/', views.risk_matrix_view, name='risk_matrix'),
    
    # فرآیند تأیید (فقط برای مدیر HSE)
    path('risk/<int:risk_id>/approve/', views.risk_approve, name='risk_approve'),
    path('risk/<int:risk_id>/reject/', views.risk_reject, name='risk_reject'),
    path('pending/', views.risk_pending_list, name='risk_pending_list'),
    
    # Import/Export Excel
    path('export/', views.risk_export_excel, name='risk_export'),
    path('import/', views.risk_import_excel, name='risk_import'),
    path('template/', views.risk_download_template, name='risk_template'),
]
