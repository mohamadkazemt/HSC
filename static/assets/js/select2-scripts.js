function initSelect2(selector, placeholder = "جستجو و انتخاب...") {
    $(selector).select2({
        placeholder: placeholder,
        allowClear: true,
        width: '100%',
        language: {
            noResults: function() {
                return "نتیجه‌ای یافت نشد";
            },
            searching: function() {
                return "در حال جستجو...";
            }
        },
        dir: "rtl"
    });
}

// تابع کمکی برای راه‌اندازی Select2 روی چندین المان
function initializeSearchableSelects() {
    // تنظیمات برای انواع مختلف select
    const selectConfigs = {
        '.personnel-select': 'جستجو و انتخاب پرسنل...',
        '.vehicle-select': 'جستجو و انتخاب خودرو...',
        '.contractor-select': 'جستجو و انتخاب پیمانکار...',
        // می‌توانید موارد بیشتری اضافه کنید
    };

    // اعمال تنظیمات روی همه select‌ها
    Object.entries(selectConfigs).forEach(([selector, placeholder]) => {
        initSelect2(selector, placeholder);
    });
}

// اجرای اتوماتیک هنگام لود صفحه
$(document).ready(function() {
    initializeSearchableSelects();
});
