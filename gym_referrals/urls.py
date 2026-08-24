from django.urls import path

from . import api, views

app_name = "gym_referrals"

# Registry consumed by the central permissions app ("مدیریت دسترسی‌ها").
# ``name`` is the permission string stored in the permission tables and must
# match the value passed to gym_access_required in the views; several URLs may
# deliberately share one name so a single grant unlocks a whole flow.
# ``url_name`` keeps historical URL names stable for reverse(). Public
# endpoints (QR verification, operator redeem) are not listed because their
# authorization is token/operator based.
URLS_WITH_LABELS = [
    {"path": "", "view": views.create_page, "url_name": "create", "name": "gym_referral_create",
     "label": "باشگاه_صدور معرفی‌نامه"},
    {"path": "history/", "view": views.history_page, "url_name": "history", "name": "gym_referral_history",
     "label": "باشگاه_سوابق معرفی‌نامه‌های من"},
    {"path": "referrals/<str:referral_number>/", "view": views.referral_detail, "url_name": "referral_detail",
     "name": "gym_referral_history", "label": "باشگاه_سوابق معرفی‌نامه‌های من"},
    {"path": "<str:referral_number>/cancel/", "view": views.cancel_page, "url_name": "cancel",
     "name": "gym_referral_history", "label": "باشگاه_سوابق معرفی‌نامه‌های من"},
    {"path": "<str:referral_number>/qr.png", "view": views.referral_qr, "url_name": "referral_qr",
     "name": "gym_referral_history", "label": "باشگاه_سوابق معرفی‌نامه‌های من"},
    {"path": "management/referrals/", "view": views.referral_admin_list, "url_name": "referral_admin_list",
     "name": "gym_referral_management", "label": "باشگاه_مدیریت معرفی‌نامه‌ها"},
    {"path": "management/legacy/", "view": views.legacy_list, "url_name": "legacy_list",
     "name": "gym_referral_management", "label": "باشگاه_مدیریت معرفی‌نامه‌ها"},
    {"path": "legacy/import/", "view": views.legacy_import, "url_name": "legacy_import",
     "name": "gym_referral_management", "label": "باشگاه_مدیریت معرفی‌نامه‌ها"},
    {"path": "management/reports/", "view": views.reports_page, "url_name": "reports",
     "name": "gym_referral_management", "label": "باشگاه_مدیریت معرفی‌نامه‌ها"},
    {"path": "management/usages/", "view": views.usage_list, "url_name": "usage_list",
     "name": "gym_referral_usage", "label": "باشگاه_استفاده‌های ثبت‌شده"},
    {"path": "management/gyms/", "view": views.gym_list, "url_name": "gym_list",
     "name": "gym_manage", "label": "باشگاه_مدیریت باشگاه‌ها"},
    {"path": "management/gyms/new/", "view": views.gym_create, "url_name": "gym_create",
     "name": "gym_manage", "label": "باشگاه_مدیریت باشگاه‌ها"},
    {"path": "management/gyms/<int:gym_id>/", "view": views.gym_detail, "url_name": "gym_detail",
     "name": "gym_manage", "label": "باشگاه_مدیریت باشگاه‌ها"},
    {"path": "management/gyms/<int:gym_id>/edit/", "view": views.gym_edit, "url_name": "gym_edit",
     "name": "gym_manage", "label": "باشگاه_مدیریت باشگاه‌ها"},
    {"path": "management/gyms/<int:gym_id>/contracts/new/", "view": views.gym_contract_create,
     "url_name": "gym_contract_create", "name": "gym_contract_manage", "label": "باشگاه_مدیریت قراردادها"},
    {"path": "management/gyms/<int:gym_id>/operators/new/", "view": views.operator_create,
     "url_name": "gym_operator_create", "name": "gym_operator_manage", "label": "باشگاه_مدیریت اپراتورها"},
    {"path": "management/contracts/", "view": views.contract_list, "url_name": "contract_list",
     "name": "gym_contract_manage", "label": "باشگاه_مدیریت قراردادها"},
    {"path": "management/contracts/new/", "view": views.contract_create, "url_name": "contract_create",
     "name": "gym_contract_manage", "label": "باشگاه_مدیریت قراردادها"},
    {"path": "management/contracts/<int:contract_id>/", "view": views.contract_detail,
     "url_name": "contract_detail", "name": "gym_contract_manage", "label": "باشگاه_مدیریت قراردادها"},
    {"path": "management/contracts/<int:contract_id>/edit/", "view": views.contract_edit,
     "url_name": "contract_edit", "name": "gym_contract_manage", "label": "باشگاه_مدیریت قراردادها"},
    {"path": "management/operators/", "view": views.operator_list, "url_name": "operator_list",
     "name": "gym_operator_manage", "label": "باشگاه_مدیریت اپراتورها"},
    {"path": "management/operators/new/", "view": views.operator_create, "url_name": "operator_create",
     "name": "gym_operator_manage", "label": "باشگاه_مدیریت اپراتورها"},
    {"path": "management/operators/<int:operator_id>/delete/", "view": views.operator_delete,
     "url_name": "operator_delete", "name": "gym_operator_manage", "label": "باشگاه_مدیریت اپراتورها"},
    {"path": "invoices/", "view": views.invoice_list, "url_name": "invoice_list",
     "name": "gym_invoice_view", "label": "باشگاه_صورتحساب‌ها"},
    {"path": "invoices/<int:invoice_id>/", "view": views.invoice_detail, "url_name": "invoice_detail",
     "name": "gym_invoice_view", "label": "باشگاه_صورتحساب‌ها"},
    {"path": "invoices/<int:invoice_id>/export.xlsx", "view": views.invoice_export_excel,
     "url_name": "invoice_export_excel", "name": "gym_invoice_view", "label": "باشگاه_صورتحساب‌ها"},
    {"path": "invoices/<int:invoice_id>/<str:status>/", "view": views.invoice_transition,
     "url_name": "invoice_transition", "name": "gym_invoice_view", "label": "باشگاه_صورتحساب‌ها"},
    {"path": "api/referrals/", "view": api.create_referral, "url_name": "api_create",
     "name": "gym_referral_create", "label": "باشگاه_صدور معرفی‌نامه"},
    {"path": "api/referrals/current/", "view": api.current_referral, "url_name": "api_current",
     "name": "gym_referral_create", "label": "باشگاه_صدور معرفی‌نامه"},
    {"path": "api/referrals/<str:referral_number>/cancel/", "view": api.cancel_referral,
     "url_name": "api_cancel", "name": "gym_referral_history", "label": "باشگاه_سوابق معرفی‌نامه‌های من"},
]

PUBLIC_URL_PATTERNS = [
    path("api/referrals/verify/<uuid:public_token>/", api.verify_referral, name="api_verify"),
    path("api/referrals/verify/<uuid:public_token>/redeem/", api.redeem_referral, name="api_redeem"),
]

urlpatterns = [path(url["path"], url["view"], name=url["url_name"]) for url in URLS_WITH_LABELS] + PUBLIC_URL_PATTERNS
