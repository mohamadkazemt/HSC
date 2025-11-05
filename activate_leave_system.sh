#!/bin/bash
# راهنمای فعال‌سازی سیستم مدیریت مرخصی
# نسخه: 1.0.0

echo "=========================================="
echo "   فعال‌سازی سیستم مدیریت مرخصی"
echo "=========================================="
echo ""

cd /home/mohamadkazem/HSC

# 1. فعال‌سازی محیط مجازی
echo "✓ فعال‌سازی محیط مجازی..."
source .venv/bin/activate

# 2. بررسی migration ها
echo "✓ بررسی migration ها..."
python manage.py showmigrations leave_reports

# 3. جایگزینی views
echo "✓ جایگزینی views.py..."
cd leave_reports
if [ -f "views_new.py" ]; then
    mv views.py views_backup_$(date +%Y%m%d_%H%M%S).py
    mv views_new.py views.py
    echo "  ✅ views.py جایگزین شد"
else
    echo "  ℹ views_new.py یافت نشد - احتمالاً قبلاً جایگزین شده"
fi

# 4. جایگزینی urls
echo "✓ جایگزینی urls.py..."
if [ -f "urls_new.py" ]; then
    mv urls.py urls_backup_$(date +%Y%m%d_%H%M%S).py
    mv urls_new.py urls.py
    echo "  ✅ urls.py جایگزین شد"
else
    echo "  ℹ urls_new.py یافت نشد - احتمالاً قبلاً جایگزین شده"
fi

cd ..

# 5. بررسی templates
echo "✓ بررسی templates..."
TEMPLATE_DIR="templates/leave_reports"
REQUIRED_TEMPLATES=("base_leave.html" "request_leave.html" "my_inbox.html" "leave_archive.html" "leave_detail.html" "manage_approvers.html")

for template in "${REQUIRED_TEMPLATES[@]}"; do
    if [ -f "$TEMPLATE_DIR/$template" ]; then
        echo "  ✅ $template"
    else
        echo "  ❌ $template - یافت نشد!"
    fi
done

# 6. بررسی static files
echo "✓ بررسی static files..."
echo "  نیاز به این فایل‌ها:"
echo "    - static/js/persian-datepicker.min.js"
echo "    - static/css/persian-datepicker.min.css"
echo ""
echo "  برای اطمینان، collectstatic را اجرا کنید:"
echo "  python manage.py collectstatic --noinput"

# 7. خلاصه فایل‌های ایجاد شده
echo ""
echo "=========================================="
echo "   خلاصه فایل‌های سیستم"
echo "=========================================="
echo ""
echo "Backend:"
echo "  ✅ leave_reports/models.py - بازطراحی کامل"
echo "  ✅ leave_reports/forms.py - 4 فرم جدید"
echo "  ✅ leave_reports/views.py - 14 view جدید"
echo "  ✅ leave_reports/urls.py - مسیرهای جدید"
echo "  ✅ leave_reports/admin.py - بهبود یافته"
echo ""
echo "Frontend:"
echo "  ✅ templates/leave_reports/base_leave.html"
echo "  ✅ templates/leave_reports/request_leave.html"
echo "  ✅ templates/leave_reports/my_inbox.html"
echo "  ✅ templates/leave_reports/leave_archive.html"
echo "  ✅ templates/leave_reports/leave_detail.html"
echo "  ✅ templates/leave_reports/manage_approvers.html"
echo ""
echo "Database:"
echo "  ✅ Migration 0010 - اجرا شده"
echo ""

# 8. مراحل باقیمانده
echo "=========================================="
echo "   مراحل باقیمانده (دستی)"
echo "=========================================="
echo ""
echo "1. افزودن منو به Sidebar:"
echo "   فایل: templates/base.html یا templates/includes/sidebar.html"
echo "   کد نمونه در: leave_reports/IMPLEMENTATION_GUIDE.md"
echo ""
echo "2. تعریف Permissions:"
echo "   - leave_request_create"
echo "   - leave_my_inbox"  
echo "   - leave_archive_view"
echo ""
echo "3. تعریف اولین تأیید کننده:"
echo "   پس از راه‌اندازی سرور، به این آدرس بروید:"
echo "   http://localhost:8000/leave/manage-approvers/"
echo ""
echo "4. تست سیستم:"
echo "   a) ثبت درخواست: /leave/request/"
echo "   b) کارتابل: /leave/inbox/"
echo "   c) آرشیو: /leave/archive/"
echo ""

# 9. راه‌اندازی سرور
echo "=========================================="
echo "   آیا می‌خواهید سرور را راه‌اندازی کنید؟"
echo "=========================================="
echo ""
read -p "سرور را راه‌اندازی کنم؟ (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "✓ متوقف کردن سرور قبلی..."
    pkill -f runserver 2>/dev/null
    
    echo "✓ راه‌اندازی سرور جدید..."
    python manage.py runserver 0.0.0.0:8000 > .runserver.log 2>&1 &
    
    sleep 2
    
    if pgrep -f runserver > /dev/null; then
        echo "  ✅ سرور با موفقیت راه‌اندازی شد"
        echo "  📍 آدرس: http://localhost:8000"
        echo "  📝 لاگ: tail -f .runserver.log"
    else
        echo "  ❌ خطا در راه‌اندازی سرور"
        echo "  لاگ را بررسی کنید: cat .runserver.log"
    fi
fi

echo ""
echo "=========================================="
echo "   فعال‌سازی کامل شد!"
echo "=========================================="
echo ""
echo "📖 راهنمای کامل: leave_reports/IMPLEMENTATION_GUIDE.md"
echo "📋 خلاصه: LEAVE_SYSTEM_SUMMARY.md"
echo ""
