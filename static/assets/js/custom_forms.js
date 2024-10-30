// تعریف stepper به عنوان یک متغیر global
let stepper;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Stepper
    stepper = new KTStepper(document.querySelector("#kt_create_account_stepper"));

    // Initialize form event handlers
    initializeFormHandlers();

    // Initialize Select2 elements
    initializeSelect2();

    // Initialize Navigation (Next, Previous, and Submit buttons)
    initializeNavigation();
});

// مدیریت فرم و جلوگیری از ارسال پیش‌فرض در مراحل میانی
function initializeFormHandlers() {
    const form = document.getElementById('kt_create_account_form');
    if (!form) return;

    form.addEventListener('submit', function(event) {
        // جلوگیری از ارسال فرم تا زمانی که به مرحله آخر نرسیده‌ایم
        if (stepper.getCurrentStepIndex() !== stepper.getTotalStepsNumber()) {
            event.preventDefault();
        }
    });
}

// تنظیمات Select2
function initializeSelect2() {
    $('.select2').select2({
        dir: "rtl",
        width: '100%',
        language: {
            noResults: function() {
                return "نتیجه‌ای یافت نشد";
            },
            searching: function() {
                return "در حال جستجو...";
            }
        },
        dropdownParent: $('#kt_create_account_stepper') // اطمینان از قرارگیری صحیح در داخل استپر
    });
}

// مدیریت دکمه‌های "ادامه"، "برگشت" و "ثبت"
function initializeNavigation() {
    // دکمه "ادامه"
    const nextButtons = document.querySelectorAll('.next-step, [data-kt-stepper-action="next"]');
    nextButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            handleNextStep();  // رفتن به مرحله بعد
        });
    });

    // دکمه "برگشت"
    const prevButtons = document.querySelectorAll('.prev-step, [data-kt-stepper-action="previous"]');
    prevButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            handlePreviousStep();  // برگشت به مرحله قبلی
        });
    });

    // دکمه "ثبت"
    const submitButton = document.querySelector('[data-kt-stepper-action="submit"]');
    if (submitButton) {
        submitButton.addEventListener('click', function(e) {
            if (stepper.getCurrentStepIndex() === stepper.getTotalStepsNumber()) {
                document.getElementById('kt_create_account_form').submit();  // ارسال فرم
            } else {
                e.preventDefault();  // جلوگیری از ارسال فرم قبل از مرحله آخر
            }
        });
    }
}

// مدیریت جابجایی به مرحله بعد
function handleNextStep() {
    const currentStep = stepper.getCurrentStepIndex();

    // اعتبارسنجی مرحله فعلی
    if (validateStep(currentStep)) {
        stepper.goNext();  // رفتن به مرحله بعد
        updateStepContent();  // به‌روزرسانی محتوای مرحله
    }
}

// مدیریت برگشت به مرحله قبلی
function handlePreviousStep() {
    stepper.goPrevious();  // به مرحله قبلی برو
    updateStepContent();  // به‌روزرسانی محتوای مرحله
}

// به‌روزرسانی محتوای مراحل بر اساس مرحله فعلی
function updateStepContent() {
    const currentStep = stepper.getCurrentStepIndex();  // شماره مرحله فعلی
    const totalSteps = stepper.getTotalStepsNumber();   // تعداد کل مراحل

    // دریافت تمام بخش‌های محتوای هر مرحله
    const stepContents = document.querySelectorAll('[data-kt-stepper-element="content"]');

    // پنهان کردن تمامی محتوای مراحل و نمایش فقط مرحله فعلی
    stepContents.forEach((content, index) => {
        if (index + 1 === currentStep) {
            content.style.display = 'block';  // نمایش محتوای مرحله فعلی
        } else {
            content.style.display = 'none';   // مخفی کردن سایر مراحل
        }
    });

    // به‌روزرسانی وضعیت دکمه‌ها (ادامه، برگشت، ثبت)
    updateNavigationVisibility();
}

// به‌روزرسانی دکمه‌های "ادامه"، "برگشت" و "ثبت"
function updateNavigationVisibility() {
    const currentStep = stepper.getCurrentStepIndex();
    const totalSteps = stepper.getTotalStepsNumber();

    const nextButton = document.querySelector('[data-kt-stepper-action="next"]');
    const prevButton = document.querySelector('[data-kt-stepper-action="previous"]');
    const submitButton = document.querySelector('[data-kt-stepper-action="submit"]');

    // نمایش یا مخفی کردن دکمه‌ها بر اساس مرحله فعلی
    if (nextButton) {
        nextButton.style.display = currentStep === totalSteps ? 'none' : '';  // مخفی کردن دکمه "ادامه" در مرحله آخر
    }
    if (prevButton) {
        prevButton.style.display = currentStep === 1 ? 'none' : '';  // مخفی کردن دکمه "برگشت" در مرحله اول
    }
    if (submitButton) {
        submitButton.style.display = currentStep === totalSteps ? '' : 'none';  // نمایش دکمه "ثبت" در مرحله آخر
    }
}

// اعتبارسنجی مراحل مختلف
function validateStep(stepNumber) {
    switch(stepNumber) {
        case 1: return true;  // اعتبارسنجی عملیات بارگیری
        case 2: return true;  // اعتبارسنجی ماشین‌آلات بارگیری
        case 3: return true;  // اعتبارسنجی مرخصی‌ها
        case 4: return true;  // اعتبارسنجی خودروها
        case 5: return true;  // اعتبارسنجی توضیحات سرشیفت
        default: return true;
    }
}

// مدیریت پیام‌های خطا
function showError(message) {
    Swal.fire({
        title: 'خطا',
        text: message,
        icon: 'error',
        confirmButtonText: 'باشه',
        customClass: {
            confirmButton: 'btn btn-primary'
        }
    });
}

// افزودن عملیات بارگیری به جدول
function addLoadingOperation() {
    const stoneType = document.getElementById('stone_type');
    const loadCount = document.getElementById('load_count');

    if (!stoneType?.value || !loadCount?.value) {
        showError('لطفا نوع سنگ و تعداد بار را وارد کنید.');
        return;
    }

    const tbody = document.querySelector('#loading_operations_table tbody');
    if (!tbody) return;

    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td>${stoneType.options[stoneType.selectedIndex].text}</td>
        <td>${loadCount.value}</td>
        <td>
            <button type="button" class="btn btn-sm btn-danger" onclick="this.closest('tr').remove()">حذف</button>
            <input type="hidden" name="loading_operations[]" value="${stoneType.value},${loadCount.value}">
        </td>
    `;
    tbody.appendChild(tr);

    // پاک کردن فیلدها
    stoneType.value = '';
    loadCount.value = '';
    $(stoneType).trigger('change');  // ریست کردن انتخاب
}

// افزودن ماشین‌آلات به جدول
function addMiningMachine() {
    const machineSelect = document.getElementById('mining_machine_id');
    const blockSelect = document.getElementById('mining_block_id');
    const status = document.getElementById('machine_status');
    const inactiveReason = document.getElementById('machine_inactive_reason');

    // بررسی اینکه آیا فیلدهای ماشین‌آلات و بلوک انتخاب شده‌اند
    if (!machineSelect?.value || !blockSelect?.value) {
        showError('لطفا ماشین‌آلات و بلوک را انتخاب کنید.');
        return;
    }

    // اگر وضعیت غیرفعال است، دلیل غیرفعال بودن هم باید وارد شود
    if (status.value === 'inactive' && !inactiveReason?.value.trim()) {
        showError('لطفا دلیل غیرفعال بودن را وارد کنید.');
        return;
    }

    const tbody = document.querySelector('#mining_machines_table tbody');
    if (!tbody) return;

    // ایجاد یک سطر جدید در جدول برای اضافه کردن ماشین‌آلات
    const tr = document.createElement('tr');
    const machineText = machineSelect.options[machineSelect.selectedIndex].text;
    const blockText = blockSelect.options[blockSelect.selectedIndex].text;

    // جدا کردن نام ماشین و پیمانکار
    const [machineName, contractorName = '-'] = machineText.split(' - ');
    const [blockName, blockType = '-'] = blockText.split(' - ');

    // اضافه کردن اطلاعات به سطر
    tr.innerHTML = `
        <td>${machineName}</td>
        <td>${contractorName}</td>
        <td>${blockName}</td>
        <td>${blockType}</td>
        <td>${status.value === 'active' ? 'فعال' : 'غیرفعال'}</td>
        <td>${inactiveReason?.value || '-'}</td>
        <td>
            <button type="button" class="btn btn-sm btn-danger" onclick="this.closest('tr').remove()">حذف</button>
            <input type="hidden" name="mining_machines[]" value="${machineSelect.value},${blockSelect.value},${status.value},${inactiveReason?.value || ''}">
        </td>
    `;

    // افزودن سطر جدید به جدول
    tbody.appendChild(tr);

    // پاک کردن فیلدهای انتخابی و ریست کردن آنها
    $(machineSelect).val('').trigger('change');
    $(blockSelect).val('').trigger('change');
    status.value = 'active';  // وضعیت به فعال برگردد
    if (inactiveReason) inactiveReason.value = '';  // فیلد دلیل غیرفعال بودن خالی شود
    document.querySelector('.machine-inactive-reason').style.display = 'none';  // مخفی کردن فیلد دلیل غیرفعال بودن
}
