let stepper;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Stepper
    const stepperElement = document.querySelector("#kt_create_account_stepper");
    if (!stepperElement) return;

    stepper = new KTStepper(stepperElement);

    // تنظیم event listener برای تغییر مرحله
    stepper.on('kt.stepper.changed', function(stepper) {
        // به‌روزرسانی محتوا زمانی که مرحله تغییر می‌کند
        const currentStepIndex = stepper.getCurrentStepIndex();
        updateStepContent(currentStepIndex);
    });

    // تنظیم event listener برای قبل از تغییر مرحله
    stepper.on('kt.stepper.next', function(stepper) {
        // اعتبارسنجی قبل از رفتن به مرحله بعد
        const currentStepIndex = stepper.getCurrentStepIndex();
        if (!validateStep(currentStepIndex)) {
            stepper.stop(); // توقف انتقال به مرحله بعد اگر اعتبارسنجی رد شود
        }
    });

    // Initialize form event handlers
    initializeFormHandlers();

    // Initialize Select2 elements
    initializeSelect2();

    // Initialize Navigation
    initializeNavigation();

    // تنظیم event listener برای تغییر وضعیت ماشین
    const machineStatus = document.getElementById('machine_status');
    if (machineStatus) {
        machineStatus.addEventListener('change', function() {
            const reasonContainer = document.querySelector('.machine-inactive-reason');
            if (reasonContainer) {
                reasonContainer.style.display = this.value === 'inactive' ? 'block' : 'none';
            }
        });
    }

    // نمایش محتوای مرحله اول در شروع
    setTimeout(() => {
        updateStepContent(1);
    }, 100);
});

function initializeFormHandlers() {
    const form = document.getElementById('kt_create_account_form');
    if (!form) return;

    form.addEventListener('submit', function(event) {
        if (stepper.getCurrentStepIndex() !== stepper.getTotalStepsNumber()) {
            event.preventDefault();
        }
    });
}

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
        dropdownParent: $('#kt_create_account_stepper')
    });
}

function initializeNavigation() {
    const nextButtons = document.querySelectorAll('[data-kt-stepper-action="next"], .next-step');
    nextButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            handleNextStep();
        });
    });

    const prevButtons = document.querySelectorAll('[data-kt-stepper-action="previous"], .prev-step');
    prevButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            handlePreviousStep();
        });
    });

    const submitButton = document.querySelector('[data-kt-stepper-action="submit"]');
    if (submitButton) {
        submitButton.addEventListener('click', function(e) {
            if (stepper.getCurrentStepIndex() === stepper.getTotalStepsNumber()) {
                document.getElementById('kt_create_account_form').submit();
            } else {
                e.preventDefault();
            }
        });
    }
}

function handleNextStep() {
    if (validateStep(stepper.getCurrentStepIndex())) {
        stepper.goNext();
    }
}

function handlePreviousStep() {
    stepper.goPrevious();
}

function updateStepContent(stepIndex) {
    // پنهان کردن همه محتواها
    const allContents = document.querySelectorAll('[data-kt-stepper-element="content"]');
    allContents.forEach(content => {
        content.style.display = 'none';
        content.classList.remove('current');
    });

    // نمایش محتوای فعلی
    const currentContent = allContents[stepIndex - 1];
    if (currentContent) {
        currentContent.style.display = 'block';
        currentContent.classList.add('current');

        // اطمینان از نمایش محتوا با استفاده از setTimeout
        setTimeout(() => {
            currentContent.style.display = 'block';
            currentContent.classList.add('current');
        }, 50);
    }

    // به‌روزرسانی وضعیت دکمه‌ها
    updateNavigationVisibility(stepIndex);
}

function updateNavigationVisibility(currentStep) {
    const totalSteps = stepper.getTotalStepsNumber();

    const nextButton = document.querySelector('[data-kt-stepper-action="next"]');
    const prevButton = document.querySelector('[data-kt-stepper-action="previous"]');
    const submitButton = document.querySelector('[data-kt-stepper-action="submit"]');

    if (nextButton) {
        nextButton.style.display = currentStep === totalSteps ? 'none' : '';
    }
    if (prevButton) {
        prevButton.style.display = currentStep === 1 ? 'none' : '';
    }
    if (submitButton) {
        submitButton.style.display = currentStep === totalSteps ? '' : 'none';
    }
}

function validateStep(stepNumber) {
    switch(stepNumber) {
        case 1:
            return validateLoadingOperations();
        case 2:
            return validateMiningMachines();
        case 3:
            return validateLeaves();
        case 4:
            return validateVehicles();
        case 5:
            return validateSupervisorComments();
        default:
            return true;
    }
}

function validateLoadingOperations() {
    const table = document.querySelector('#loading_operations_table tbody');
    if (!table || table.children.length === 0) {
        showError('لطفاً حداقل یک عملیات بارگیری را اضافه کنید');
        return false;
    }
    return true;
}

function validateMiningMachines() {
    const table = document.querySelector('#mining_machines_table tbody');
    if (!table || table.children.length === 0) {
        showError('لطفاً حداقل یک ماشین‌آلات را اضافه کنید');
        return false;
    }
    return true;
}

function validateLeaves() {
    const table = document.querySelector('#leaves_table tbody');
    if (!table || table.children.length === 0) {
        showError('لطفاً حداقل یک مرخصی را اضافه کنید');
        return false;
    }
    return true;
}

function validateVehicles() {
    const table = document.querySelector('#vehicles_table tbody');
    if (!table || table.children.length === 0) {
        showError('لطفاً حداقل یک خودرو را اضافه کنید');
        return false;
    }
    return true;
}

function validateSupervisorComments() {
    const comments = document.querySelector('#supervisor_comments')?.value;
    if (!comments?.trim()) {
        showError('لطفاً توضیحات سرشیفت را وارد کنید');
        return false;
    }
    return true;
}

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

// توابع اضافه کردن آیتم‌ها
function addLoadingOperation() {
    const stoneType = document.getElementById('stone_type');
    const loadCount = document.getElementById('load_count');

    if (!stoneType?.value || !loadCount?.value) {
        showError('لطفا نوع سنگ و تعداد بار را وارد کنید.');
        return;
    }

    const loadCountValue = parseInt(loadCount.value);
    if (isNaN(loadCountValue) || loadCountValue <= 0) {
        showError('لطفا تعداد بار معتبر وارد کنید.');
        return;
    }

    const tbody = document.querySelector('#loading_operations_table tbody');
    if (!tbody) {
        showError('جدول عملیات بارگیری یافت نشد.');
        return;
    }

    try {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${stoneType.options[stoneType.selectedIndex].text}</td>
            <td>${loadCountValue}</td>
            <td>
                <button type="button" class="btn btn-sm btn-danger" onclick="removeTableRow(this)">حذف</button>
                <input type="hidden" name="loading_operations[]" value="${stoneType.value},${loadCountValue}">
            </td>
        `;
        tbody.appendChild(tr);

        // پاک کردن فیلدها
        stoneType.value = '';
        loadCount.value = '';
        if ($(stoneType).hasClass('select2-hidden-accessible')) {
            $(stoneType).trigger('change');
        }

    } catch (error) {
        console.error('Error in addLoadingOperation:', error);
        showError('خطا در افزودن عملیات بارگیری');
    }
}

function addMiningMachine() {
    const machineSelect = document.getElementById('mining_machine_id');
    const blockSelect = document.getElementById('mining_block_id');
    const status = document.getElementById('machine_status');
    const inactiveReason = document.getElementById('machine_inactive_reason');

    if (!machineSelect?.value || !blockSelect?.value) {
        showError('لطفا ماشین‌آلات و بلوک را انتخاب کنید.');
        return;
    }

    if (status.value === 'inactive' && !inactiveReason?.value.trim()) {
        showError('لطفا دلیل غیرفعال بودن را وارد کنید.');
        return;
    }

    const tbody = document.querySelector('#mining_machines_table tbody');
    if (!tbody) {
        showError('جدول ماشین‌آلات یافت نشد.');
        return;
    }

    try {
        const tr = document.createElement('tr');
        const machineText = machineSelect.options[machineSelect.selectedIndex].text;
        const blockText = blockSelect.options[blockSelect.selectedIndex].text;

        const [machineName, contractorName = '-'] = machineText.split(' - ');
        const [blockName, blockType = '-'] = blockText.split(' - ');

        tr.innerHTML = `
            <td>${machineName}</td>
            <td>${contractorName}</td>
            <td>${blockName}</td>
            <td>${blockType}</td>
            <td>${status.value === 'active' ? 'فعال' : 'غیرفعال'}</td>
            <td>${inactiveReason?.value || '-'}</td>
            <td>
                <button type="button" class="btn btn-sm btn-danger" onclick="removeTableRow(this)">حذف</button>
                <input type="hidden" name="mining_machines[]" value="${machineSelect.value},${blockSelect.value},${status.value},${inactiveReason?.value || ''}">
            </td>
        `;

        tbody.appendChild(tr);

        // پاک کردن فیلدها
        $(machineSelect).val('').trigger('change');
        $(blockSelect).val('').trigger('change');
        status.value = 'active';
        if (inactiveReason) inactiveReason.value = '';
        document.querySelector('.machine-inactive-reason').style.display = 'none';

    } catch (error) {
        console.error('Error in addMiningMachine:', error);
        showError('خطا در افزودن ماشین‌آلات');
    }
}

function addLeave() {
    const personnelSelect = document.getElementById('personnel_id');
    const leaveStatus = document.getElementById('leave_status');

    if (!personnelSelect?.value) {
        showError('لطفا پرسنل را انتخاب کنید.');
        return;
    }

    const tbody = document.querySelector('#leaves_table tbody');
    if (!tbody) {
        showError('جدول مرخصی‌ها یافت نشد.');
        return;
    }

    try {
        const tr = document.createElement('tr');
        const personnelText = personnelSelect.options[personnelSelect.selectedIndex].text;
        const [personnelName, personnelCode = '-'] = personnelText.split(' - ');

        tr.innerHTML = `
            <td>${personnelName}</td>
            <td>${personnelCode}</td>
            <td>${leaveStatus.value === 'authorized' ? 'مجاز' : 'غیر مجاز'}</td>
            <td>
                <button type="button" class="btn btn-sm btn-danger" onclick="removeTableRow(this)">حذف</button>
                <input type="hidden" name="leaves[]" value="${personnelSelect.value},${leaveStatus.value}">
            </td>
        `;

        tbody.appendChild(tr);

        // پاک کردن فیلدها
        $(personnelSelect).val('').trigger('change');
        leaveStatus.value = 'unauthorized';

    } catch (error) {
        console.error('Error in addLeave:', error);
        showError('خطا در افزودن مرخصی');
    }
}

function addVehicle() {
    const vehicleSelect = document.getElementById('vehicle_id');

    if (!vehicleSelect?.value) {
        showError('لطفا خودرو را انتخاب کنید.');
        return;
    }

    const tbody = document.querySelector('#vehicles_table tbody');
    if (!tbody) {
        showError('جدول خودروها یافت نشد.');
        return;
    }

    try {
        const tr = document.createElement('tr');
        const vehicleText = vehicleSelect.options[vehicleSelect.selectedIndex].text;
        const [vehicleName, contractorName, vehicleType] = vehicleText.split(' - ');

        tr.innerHTML = `
            <td>${vehicleName}</td>
            <td>${contractorName || '-'}</td>
            <td>${vehicleName}</td>
            <td>${contractorName || '-'}</td>
            <td>${vehicleType || '-'}</td>
            <td>
                <button type="button" class="btn btn-sm btn-danger" onclick="removeTableRow(this)">حذف</button>
                <input type="hidden" name="vehicles[]" value="${vehicleSelect.value}">
            </td>
        `;

        tbody.appendChild(tr);

        // پاک کردن فیلد
        $(vehicleSelect).val('').trigger('change');

    } catch (error) {
        console.error('Error in addVehicle:', error);
        showError('خطا در افزودن خودرو');
    }
}

// تابع حذف سطر از جدول
function removeTableRow(button) {
    try {
        const row = button.closest('tr');
        if (row) {
            row.remove();
        }
    } catch (error) {
        console.error('Error in removeTableRow:', error);
        showError('خطا در حذف سطر');
    }
}

// تابع کمکی برای نمایش پیام موفقیت
function showSuccess(message) {
    Swal.fire({
        title: 'موفقیت',
        text: message,
        icon: 'success',
        confirmButtonText: 'باشه',
        customClass: {
            confirmButton: 'btn btn-primary'
        }
    });
}

// تابع کمکی برای نمایش پیام تأیید
function showConfirm(message, callback) {
    Swal.fire({
        title: 'تأیید',
        text: message,
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'بله',
        cancelButtonText: 'خیر',
        customClass: {
            confirmButton: 'btn btn-primary',
            cancelButton: 'btn btn-secondary'
        }
    }).then((result) => {
        if (result.isConfirmed && callback) {
            callback();
        }
    });
}

// تابع برای بررسی وضعیت فرم قبل از ارسال
function validateForm() {
    const currentStep = stepper.getCurrentStepIndex();
    const totalSteps = stepper.getTotalStepsNumber();

    if (currentStep === totalSteps) {
        // بررسی تمام مراحل قبل از ارسال نهایی
        for (let i = 1; i <= totalSteps; i++) {
            if (!validateStep(i)) {
                stepper.goTo(i);
                return false;
            }
        }
        return true;
    }
    return false;
}

// اضافه کردن event listener برای نمایش/مخفی کردن فیلد دلیل غیرفعال بودن
document.addEventListener('DOMContentLoaded', function() {
    const machineStatus = document.getElementById('machine_status');
    if (machineStatus) {
        machineStatus.addEventListener('change', function() {
            const reasonContainer = document.querySelector('.machine-inactive-reason');
            if (reasonContainer) {
                reasonContainer.style.display = this.value === 'inactive' ? 'block' : 'none';
            }
        });
    }
});

// مدیریت ارسال فرم
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('kt_create_account_form');
    if (form) {
        form.addEventListener('submit', function(e) {
            if (!validateForm()) {
                e.preventDefault();
                return false;
            }
        });
    }
});

// تابع برای پاک کردن تمام فیلدهای یک فرم
function resetForm(formElement) {
    if (!formElement) return;

    // پاک کردن input های معمولی
    formElement.querySelectorAll('input:not([type="hidden"])').forEach(input => {
        input.value = '';
    });

    // پاک کردن select ها
    formElement.querySelectorAll('select').forEach(select => {
        if ($(select).hasClass('select2-hidden-accessible')) {
            $(select).val('').trigger('change');
        } else {
            select.selectedIndex = 0;
        }
    });

    // پاک کردن textarea ها
    formElement.querySelectorAll('textarea').forEach(textarea => {
        textarea.value = '';
    });
}

// تابع برای بررسی اعتبار فایل آپلود شده
function validateFile(file) {
    if (!file) return true;

    // بررسی حجم فایل (حداکثر 5MB)
    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
        showError('حجم فایل نباید بیشتر از 5 مگابایت باشد.');
        return false;
    }

    // بررسی پسوند فایل
    const allowedTypes = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png'];
    const fileName = file.name.toLowerCase();
    const fileExtension = '.' + fileName.split('.').pop();

    if (!allowedTypes.includes(fileExtension)) {
        showError('فرمت فایل مجاز نیست. فرمت‌های مجاز: PDF, Word, JPG');
        return false;
    }

    return true;
}

// مدیریت آپلود فایل
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file && !validateFile(file)) {
                this.value = ''; // پاک کردن انتخاب فایل در صورت نامعتبر بودن
            }
        });
    }
});