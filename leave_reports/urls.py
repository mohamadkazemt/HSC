from django.urls import path
from . import views

app_name = 'leave_reports'

URLS_WITH_LABELS = [
    # درخواست مرخصی جدید
    {
        "path": "request/",
        "view": views.request_leave,
        "name": "request_leave",
        "label": "مرخصی_درخواست جدید",
    },
    
    # کارتابل من
    {
        "path": "inbox/",
        "view": views.my_inbox,
        "name": "my_inbox",
        "label": "مرخصی_کارتابل",
    },
    
    # آرشیو مرخصی‌ها
    {
        "path": "archive/",
        "view": views.leave_archive,
        "name": "leave_archive",
        "label": "مرخصی_آرشیو",
    },
    
    # جزئیات درخواست
    {
        "path": "detail/<int:leave_id>/",
        "view": views.leave_detail,
        "name": "leave_detail",
        "label": "مرخصی_جزئیات",
    },
    
    # تأیید/رد توسط جایگزین
    {
        "path": "approve-replacement/<int:leave_id>/",
        "view": views.approve_as_replacement,
        "name": "approve_as_replacement",
        "label": "مرخصی_تأیید جایگزین",
    },
    {
        "path": "reject-replacement/<int:leave_id>/",
        "view": views.reject_as_replacement,
        "name": "reject_as_replacement",
        "label": "مرخصی_رد جایگزین",
    },
    
    # تأیید/رد توسط مدیر
    {
        "path": "approve-manager/<int:leave_id>/",
        "view": views.approve_as_manager,
        "name": "approve_as_manager",
        "label": "مرخصی_تأیید مدیر",
    },
    {
        "path": "reject-manager/<int:leave_id>/",
        "view": views.reject_as_manager,
        "name": "reject_as_manager",
        "label": "مرخصی_رد مدیر",
    },
    
    # مدیریت تأیید کنندگان
    {
        "path": "manage-approvers/",
        "view": views.manage_approvers,
        "name": "manage_approvers",
        "label": "مرخصی_مدیریت تأیید کنندگان",
    },
    {
        "path": "delete-approver/<int:hierarchy_id>/",
        "view": views.delete_approver,
        "name": "delete_approver",
        "label": "مرخصی_حذف تأیید کننده",
    },
    
    # API endpoints
    {
        "path": "api/users-for-replacement/",
        "view": views.api_get_users_for_replacement,
        "name": "api_users_for_replacement",
        "label": "مرخصی_API لیست جایگزین‌ها",
    },
    {
        "path": "api/user-profiles/",
        "view": views.api_get_user_profiles,
        "name": "api_user_profiles",
        "label": "مرخصی_API لیست پروفایل کاربران",
    },
    {
        "path": "api/parts-by-section/",
        "view": views.api_get_parts_by_section,
        "name": "api_parts_by_section",
        "label": "مرخصی_API قسمت‌ها بر اساس بخش",
    },
]

urlpatterns = [path(item["path"], item["view"], name=item["name"]) for item in URLS_WITH_LABELS]
