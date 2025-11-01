from django.urls import path
from . import views

app_name = 'contractor_management'

URLS_WITH_LABELS = [
    {
        "path": "dashboard/",
        "view": views.contractor_dashboard,
        "name": "contractor_dashboard",
        "label": "پیمانکاران-داشبورد مدیریت",
    },
    {
        "path": "contractor-login/",
        "view": views.contractor_login,
        "name": "contractor_login",
        "label": "پیمانکاران-ورود کاربران",
    },
    {
        "path": "contractor-portal/",
        "view": views.contractor_portal_dashboard,
        "name": "contractor_portal",
        "label": "پیمانکاران-پورتال کاربری",
    },
    {
        "path": "manage-employees/",
        "view": views.manage_employees,
        "name": "manage_employees",
        "label": "پیمانکاران-مدیریت پرسنل",
    },
    {
        "path": "manage-employees/<int:pk>/credentials/",
        "view": views.contractor_employee_credentials,
        "name": "contractor_employee_credentials",
        "label": "پیمانکاران-نامه کاربری پرسنل",
    },
    {
        "path": "manage-employees/<int:pk>/edit/",
        "view": views.contractor_employee_edit,
        "name": "contractor_employee_edit",
        "label": "پیمانکاران-ویرایش پرسنل توسط پیمانکار",
    },
    {
        "path": "manage-employees/<int:pk>/delete/",
        "view": views.contractor_employee_delete,
        "name": "contractor_employee_delete",
        "label": "پیمانکاران-حذف پرسنل توسط پیمانکار",
    },
    {
        "path": "manage-employees/<int:pk>/reset-password/",
        "view": views.contractor_employee_reset_password,
        "name": "contractor_employee_reset_password",
        "label": "پیمانکاران-بازنشانی رمز پرسنل",
    },
    {
        "path": "manage-vehicles/",
        "view": views.manage_vehicles,
        "name": "manage_vehicles",
        "label": "پیمانکاران-مدیریت خودروها",
    },
    {
        "path": "contractor-profile/",
        "view": views.contractor_profile_documents,
        "name": "contractor_profile",
        "label": "پیمانکاران-پروفایل و مدارک",
    },
    {
        "path": "create-report/",
        "view": views.create_report,
        "name": "create_report",
        "label": "پیمانکاران-ایجاد گزارش کارکرد خودروها",
    },
    {
        "path": "reports/",
        "view": views.all_reports,
        "name": "all_reports",
        "label": "پیمانکاران-گزارشگیری خودرو ها",
    },
    {
        "path": "reports/list/",
        "view": views.report_list,
        "name": "report_list",
        "label": "پیمانکاران-لیست گزارش‌ها",
    },
    {
        "path": "report/<int:pk>/",
        "view": views.report_detail,
        "name": "report_detail",
        "label": "پیمانکاران-جزئیات گزارش کارکرد خودرو",
    },
    {
        "path": "get_contractors_ajax/",
        "view": views.get_contractors_ajax,
        "name" : "get_contractors_ajax",
        "label": "پیمانکاران-دریافت پیمانکاران",
    },
    {
        "path": "get_contractor_employees_ajax/",
        "view": views.get_contractor_employees_ajax,
        "name": "get_contractor_employees_ajax",
        "label": "پیمانکاران-دریافت پیمانکاران",
    },
    {
        "path": "get-all-vehicles-ajax/",
        "view": views.get_all_vehicles_ajax,
        "name": "get_all_vehicles_ajax",
        "label": "پیمانکاران-دریافت خودروها",
    },
    {
        "path": "vehicle/<int:vehicle_id>/reports/",
        "view": views.vehicle_reports,
        "name": "vehicle_reports",
        "label": "پیمانکاران-گزارش‌های کارکرد خودرو",
    },
    {
        "path": "vehicle/<int:vehicle_id>/reports/pdf/",
        "view": views.vehicle_reports_pdf,
        "name": "vehicle_reports_pdf",
        "label": "پیمانکاران-PDF گزارش‌های خودرو",
    },
    {
        "path": "vehicle/<int:pk>/",
        "view": views.vehicle_detail,
        "name": "vehicle_detail",
        "label": "پیمانکاران-جزئیات خودرو",
    },
    {
        "path": "contractor/<int:pk>/",
        "view": views.contractor_detail,
        "name": "contractor_detail",
        "label": "پیمانکاران-جزئیات پیمانکار",
    },
    {
        "path": "export-reports/",
        "view": views.export_reports_to_excel,
        "name": "export_reports",
        "label": "پیمانکاران-خروجی اکسل گزارش‌ها",
    },
    {
        "path": "export-vehicle-reports/<int:vehicle_id>/",
        "view": views.export_reports_to_excel,
        "name": "export_vehicle_reports",
        "label": "پیمانکاران-خروجی اکسل گزارش‌های خودرو",
    },
    {
        "path": "data-management/",
        "view": views.data_management,
        "name": "data_management",
        "label": "پیمانکاران-مدیریت اطلاعات پایه",
    },
    {
        "path": "manage-contractor-user/<int:pk>/",
        "view": views.manage_contractor_user,
        "name": "manage_contractor_user",
        "label": "پیمانکاران-مدیریت حساب کاربری پیمانکار",
    },
    {
        "path": "employee/<int:pk>/reset-password/",
        "view": views.reset_employee_password,
        "name": "reset_employee_password",
        "label": "پیمانکاران-ریست رمز کاربر کارمند",
    },
    # Contractor CRUD
    {
        "path": "contractor/create/",
        "view": views.contractor_create,
        "name": "contractor_create",
        "label": "پیمانکاران-ایجاد پیمانکار",
    },
    {
        "path": "contractor/<int:pk>/edit/",
        "view": views.contractor_edit,
        "name": "contractor_edit",
        "label": "پیمانکاران-ویرایش پیمانکار",
    },
    {
        "path": "contractor/<int:pk>/delete/",
        "view": views.contractor_delete,
        "name": "contractor_delete",
        "label": "پیمانکاران-حذف پیمانکار",
    },
    # Employee CRUD
    {
        "path": "employee/create/",
        "view": views.employee_create,
        "name": "employee_create",
        "label": "پیمانکاران-ایجاد کارمند",
    },
    {
        "path": "employee/<int:pk>/edit/",
        "view": views.employee_edit,
        "name": "employee_edit",
        "label": "پیمانکاران-ویرایش کارمند",
    },
    {
        "path": "employee/<int:pk>/delete/",
        "view": views.employee_delete,
        "name": "employee_delete",
        "label": "پیمانکاران-حذف کارمند",
    },
    # Vehicle CRUD
    {
        "path": "vehicle/create/",
        "view": views.vehicle_create,
        "name": "vehicle_create",
        "label": "پیمانکاران-ایجاد خودرو",
    },
    {
        "path": "vehicle/<int:pk>/edit/",
        "view": views.vehicle_edit,
        "name": "vehicle_edit",
        "label": "پیمانکاران-ویرایش خودرو",
    },
    {
        "path": "vehicle/<int:pk>/delete/",
        "view": views.vehicle_delete,
        "name": "vehicle_delete",
        "label": "پیمانکاران-حذف خودرو",
    },
    # Import/Export
    {
        "path": "export/<str:model_type>/",
        "view": views.export_data,
        "name": "export_data",
        "label": "پیمانکاران-خروجی اکسل",
    },
    {
        "path": "import/<str:model_type>/",
        "view": views.import_data,
        "name": "import_data",
        "label": "پیمانکاران-ورودی اکسل",
    },
    {
        "path": "download-template/<str:model_type>/",
        "view": views.download_template,
        "name": "download_template",
        "label": "پیمانکاران-دانلود الگو",
    },
]


urlpatterns = [
    path(url["path"], url["view"], name=url["name"]) for url in URLS_WITH_LABELS
]

