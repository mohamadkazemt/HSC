# اسکریپت PowerShell برای آپلود فایل‌ها به سرور
# استفاده: .\upload_to_server.ps1

$SERVER = "root@65.109.220.72"
$LOCAL_PATH = "D:\MKT\HSC"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "آپلود فایل‌های تنظیمات به سرور" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# بررسی وجود SCP
try {
    $null = Get-Command scp -ErrorAction Stop
} catch {
    Write-Host "خطا: scp یافت نشد!" -ForegroundColor Red
    Write-Host "لطفاً OpenSSH Client را نصب کنید." -ForegroundColor Yellow
    exit 1
}

Write-Host "`nآیا می‌خواهید فایل‌های تنظیمات را به سرور آپلود کنید؟" -ForegroundColor Yellow
Write-Host "سرور: $SERVER" -ForegroundColor White
$confirm = Read-Host "بله (y) / خیر (n)"

if ($confirm -ne 'y' -and $confirm -ne 'Y') {
    Write-Host "عملیات لغو شد." -ForegroundColor Yellow
    exit 0
}

Write-Host "`n[1/4] آپلود تنظیمات Nginx..." -ForegroundColor Green
scp "$LOCAL_PATH\nginx_config_updated.conf" "${SERVER}:/root/"
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ موفق" -ForegroundColor Green
} else {
    Write-Host "  ✗ خطا!" -ForegroundColor Red
}

Write-Host "`n[2/4] آپلود اسکریپت اعمال تنظیمات..." -ForegroundColor Green
scp "$LOCAL_PATH\apply_server_config.sh" "${SERVER}:/root/"
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ موفق" -ForegroundColor Green
} else {
    Write-Host "  ✗ خطا!" -ForegroundColor Red
}

Write-Host "`n[3/4] آپلود اسکریپت بررسی کدهای پرسنلی..." -ForegroundColor Green
scp "$LOCAL_PATH\check_personnel_codes.py" "${SERVER}:/var/www/HSC/"
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ موفق" -ForegroundColor Green
} else {
    Write-Host "  ✗ خطا!" -ForegroundColor Red
}

Write-Host "`n[4/4] آپلود راهنما..." -ForegroundColor Green
scp "$LOCAL_PATH\QUICK_FIX_GUIDE.md" "${SERVER}:/root/"
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ موفق" -ForegroundColor Green
} else {
    Write-Host "  ✗ خطا!" -ForegroundColor Red
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "آپلود کامل شد!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`nمراحل بعدی:" -ForegroundColor Yellow
Write-Host "  1. اتصال به سرور: ssh $SERVER" -ForegroundColor White
Write-Host "  2. اجرای اسکریپت: cd /root && chmod +x apply_server_config.sh && ./apply_server_config.sh" -ForegroundColor White
Write-Host "  3. Deploy کد Django: cd /var/www/HSC && git pull origin mkt && systemctl restart gunicorn" -ForegroundColor White
Write-Host ""

Write-Host "آیا می‌خواهید الان به سرور متصل شوید؟" -ForegroundColor Yellow
$connect = Read-Host "بله (y) / خیر (n)"

if ($connect -eq 'y' -or $connect -eq 'Y') {
    Write-Host "`nاتصال به سرور..." -ForegroundColor Green
    ssh $SERVER
}
