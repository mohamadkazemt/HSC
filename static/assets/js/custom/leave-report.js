let stepper;

// اول از همه تابع validation رو تعریف می‌کنیم
function validateCurrentStep(stepIndex) {
    switch(stepIndex) {
        case 1: // مرخصی عادی
            return document.querySelector('#regular_leave_table tbody').children.length > 0 ||
                confirm('هیچ مرخصی عادی ثبت نشده است. آیا مایل به ادامه هستید؟');
        case 2: // غیبت
            return document.querySelector('#absence_table tbody').children.length > 0 ||
                confirm('هیچ غیبتی ثبت نشده است. آیا مایل به ادامه هستید؟');
        case 3: // مرخصی استعلاجی
            return document.querySelector('#sick_leave_table tbody').children.length > 0 ||
                confirm('هیچ مرخصی استعلاجی ثبت نشده است. آیا مایل به ادامه هستید؟');
        case 4: // مرخصی ساعتی
            return document.querySelector('#hourly_leave_table tbody').children.length > 0 ||
                confirm('هیچ مرخصی ساعتی ثبت نشده است. آیا مایل به ادامه هستید؟');
        default:
            return true;
    }
}


document.addEventListener('DOMContentLoaded', function() {
    initializeStepper();
    initializeFormHandlers();
    initializeSelect2();

    setTimeout(() => {
        updateStepContent(1);
    }, 100);
});

function initializeStepper() {
    const stepperElement = document.querySelector("#kt_leave_stepper");
    if (!stepperElement) {
        console.error("Stepper element not found");
        return;
    }
    stepper = new KTStepper(stepperElement);

    document.querySelectorAll('[data-kt-stepper-action="next"]').forEach(btn =>
        btn.addEventListener('click', handleNextStep));

    document.querySelectorAll('[data-kt-stepper-action="previous"]').forEach(btn =>
        btn.addEventListener('click', handlePreviousStep));
}

function initializeFormHandlers() {
    const form = document.getElementById('kt_leave_form');
    if (!form) {
        console.error("Form element not found");
        return;
    }

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        if (validateAllSteps()) {
            submitLeaveReport(this);
        }
    });
}

function initializeSelect2() {
    $('.select2').select2({
        dir: "rtl",
        width: '100%',
        language: {
            noResults: () => "نتیجه‌ای یافت نشد",
            searching: () => "در حال جستجو..."
        },
        dropdownParent: $('#kt_leave_stepper'),
        selectionCssClass: 'form-select form-select-solid'
    });
}

function addRegularLeave() {
    const userSelect = document.querySelector('[name="regular_leave_user"]');

    if (!userSelect) {
        console.error("Required elements not found");
        return;
    }

    if (!userSelect.value) {
        showError('لطفا تمامی فیلدها را پر کنید');
        return;
    }

    const tbody = document.querySelector('#regular_leave_table tbody');
    if (!tbody) {
        console.error("Table body not found");
        return;
    }

    const userName = userSelect.options[userSelect.selectedIndex].text;

    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td>${userName}</td>
        <td>تاریخ ثبت خودکار</td>
        <td>
            <button type="button" class="btn btn-sm btn-danger" onclick="this.closest('tr').remove()">حذف</button>
            <input type="hidden" name="regular_leaves[]" value="${userSelect.value}">
        </td>
    `;
    tbody.appendChild(tr);

    userSelect.value = '';
    $(userSelect).trigger('change');
}


function addAbsence() {
    const userSelect = document.querySelector('[name="absence_user"]');

    if (!userSelect) {
        console.error("Required elements not found");
        return;
    }

    if (!userSelect.value) {
        showError('لطفا تمامی فیلدها را پر کنید');
        return;
    }

    const tbody = document.querySelector('#absence_table tbody');
    if (!tbody) {
        console.error("Table body not found");
        return;
    }

    const userName = userSelect.options[userSelect.selectedIndex].text;
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td>${userName}</td>
        <td>تاریخ ثبت خودکار</td>
         <td>
            <label class="form-label">توضیحات</label>
             <input type="text" class="form-control" name="absence_description[]" required>
        </td>
        <td>
            <button type="button" class="btn btn-sm btn-danger" onclick="this.closest('tr').remove()">حذف</button>
            <input type="hidden" name="absences[]" value="${userSelect.value}">
        </td>
    `;
    tbody.appendChild(tr);

    userSelect.value = '';
    $(userSelect).trigger('change');
}
function addSickLeave() {
        const userSelect = document.querySelector('[name="sick_leave_user"]');

        if (!userSelect) {
            console.error("Required elements not found");
            return;
        }

        if (!userSelect.value) {
            showError('لطفا تمامی فیلدها را پر کنید');
            return;
        }

        const tbody = document.querySelector('#sick_leave_table tbody');
        if (!tbody) {
            console.error("Table body not found");
            return;
        }

        const userName = userSelect.options[userSelect.selectedIndex].text;

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${userName}</td>
            <td>تاریخ ثبت خودکار</td>
            <td>
                <label class="form-label">توضیحات</label>
                <input type="text" class="form-control" name="sick_leave_description[]" required>
            </td>
             <td>
                <button type="button" class="btn btn-sm btn-danger" onclick="this.closest('tr').remove()">حذف</button>
                <input type="hidden" name="sick_leaves[]" value="${userSelect.value}">
             </td>
        `;
         tbody.appendChild(tr);

        userSelect.value = '';
        $(userSelect).trigger('change');
    }


function addHourlyLeave() {
    const userSelect = document.querySelector('[name="hourly_leave_user"]');
    const startTime = document.querySelector('[name="start_time"]');
    const endTime = document.querySelector('[name="end_time"]');

    if (!userSelect || !startTime || !endTime) {
        console.error("Required elements not found");
        return;
    }

    if (!userSelect.value || !startTime.value || !endTime.value) {
        showError('لطفا تمامی فیلدها را پر کنید');
        return;
    }

    const tbody = document.querySelector('#hourly_leave_table tbody');
    if (!tbody) {
        console.error("Table body not found");
        return;
    }

    const userName = userSelect.options[userSelect.selectedIndex].text;

    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td>${userName}</td>
        <td>تاریخ ثبت خودکار</td>
        <td>${startTime.value}</td>
        <td>${endTime.value}</td>
        <td>
            <button type="button" class="btn btn-sm btn-danger" onclick="this.closest('tr').remove()">حذف</button>
            <input type="hidden" name="hourly_leaves[]" value="${userSelect.value},${startTime.value},${endTime.value}">
        </td>
    `;
    tbody.appendChild(tr);

    userSelect.value = '';
    startTime.value = '';
    endTime.value = '';
    $(userSelect).trigger('change');
}


function handleNextStep() {
    console.log('Current step:', stepper.getCurrentStepIndex());

    if (validateCurrentStep(stepper.getCurrentStepIndex())) {
        console.log('Validation passed, going to next step');
        stepper.goNext();
        updateStepContent(stepper.getCurrentStepIndex());
    } else {
        console.log('Validation failed');
    }
}

function handlePreviousStep() {
    stepper.goPrevious();
    updateStepContent(stepper.getCurrentStepIndex());
}

function updateStepContent(stepIndex) {
    const contents = document.querySelectorAll('[data-kt-stepper-element="content"]');

    if (!contents.length) {
        console.error("Step contents not found");
        return;
    }

    contents.forEach(content => {
        content.style.display = 'none';
        content.classList.remove('current');
    });

    const currentContent = contents[stepIndex - 1];
    if (currentContent) {
        currentContent.style.display = 'block';
        currentContent.classList.add('current');
    } else {
        console.error("Current step content not found");
    }

    updateNavigationButtons(stepIndex);
}

function updateNavigationButtons(stepIndex) {
    const totalSteps = getTotalSteps();
    const nextBtn = document.querySelector('[data-kt-stepper-action="next"]');
    const prevBtn = document.querySelector('[data-kt-stepper-action="previous"]');
    const submitBtn = document.querySelector('[data-kt-stepper-action="submit"]');

    if (nextBtn) nextBtn.style.display = stepIndex === totalSteps ? 'none' : 'block';
    if (prevBtn) prevBtn.style.display = stepIndex === 1 ? 'none' : 'block';
    if (submitBtn) submitBtn.style.display = stepIndex === totalSteps ? 'block' : 'none';
}

function validateAllSteps() {
     const regularLeaveCount = document.querySelector('#regular_leave_table tbody').children.length;
    const absenceCount = document.querySelector('#absence_table tbody').children.length;
    const sickLeaveCount = document.querySelector('#sick_leave_table tbody').children.length;
    const hourlyLeaveCount = document.querySelector('#hourly_leave_table tbody').children.length;


    if (!regularLeaveCount && !absenceCount && !hourlyLeaveCount && !sickLeaveCount) {
         showError('لطفا حداقل یک مورد مرخصی را ثبت کنید');
        return false;
    }
    return true;
}

function getTotalSteps() {
    return document.querySelectorAll('[data-kt-stepper-element="content"]').length;
}

function submitLeaveReport(form) {
    const formData = new FormData();
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // جمع‌آوری داده‌ها
    const leaves = [];
    const tables = {
        'regular': {
            selector: '[name="regular_leaves[]"]',
            type: 'regular'
        },
        'absence': {
            selector: '[name="absences[]"]',
            type: 'absence',
            descriptionSelector: '[name="absence_description[]"]'
        },
         'sick_leave': {
            selector: '[name="sick_leaves[]"]',
            type: 'sick_leave',
            descriptionSelector: '[name="sick_leave_description[]"]'
        },
        'hourly': {
            selector: '[name="hourly_leaves[]"]',
            type: 'hourly'
        }
    };

    // جمع‌آوری داده‌ها از هر جدول
     for (const [key, table] of Object.entries(tables)) {
            const elements = document.querySelectorAll(table.selector);
            elements.forEach((input, index) => {
                const values = input.value.split(',');
                 const leaveData = {
                user: values[0],
                leave_type: table.type,
            };

                 if (table.type === 'hourly') {
                    leaveData.start_time = values[1];
                    leaveData.end_time = values[2];
                }
                if (table.descriptionSelector) {
                    const descriptionInputs = document.querySelectorAll(table.descriptionSelector);
                     if (descriptionInputs[index] && descriptionInputs[index].value) {
                        leaveData.description = descriptionInputs[index].value;
                    } else {
                         showError('لطفا توضیحات مربوط به مرخصی غیبت یا استعلاجی را وارد کنید');
                           return;
                    }
                }

              leaves.push(leaveData);

            });
        }

    // چک کردن اگر هیچ موردی ثبت نشده
    if (leaves.length === 0) {
        showError('لطفا حداقل یک مورد را ثبت کنید');
        return;
    }

    console.log('All leaves to be submitted:', leaves); // برای دیباگ

    // تبدیل به فرمت مورد نیاز برای ارسال
    leaves.forEach((leave, index) => {
        Object.entries(leave).forEach(([key, value]) => {
            formData.append(`${key}_${index}`, value);
        });
    });

    // تعداد کل موارد را هم ارسال می‌کنیم
    formData.append('total_leaves', leaves.length);

    const submitBtn = document.querySelector('[data-kt-stepper-action="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> در حال ارسال...';
    }

    // نمایش داده‌های ارسالی در کنسول برای دیباگ
    for (let [key, value] of formData.entries()) {
        console.log(`${key}: ${value}`);
    }

    $.ajax({
        url: form.action || window.location.href,
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        headers: { 'X-CSRFToken': csrftoken },
         success: function(response) {
            console.log('Response:', response); // برای دیباگ
            if (response.success) {
                handleSubmitResponse(response);
            } else {
                 handleSubmitError(response.details || response.error || 'خطا در ثبت اطلاعات');
            }
        },
         error: function(xhr, status, error) {
            console.error('Error:', error); // برای دیباگ
            handleSubmitError('خطا در ارسال اطلاعات. لطفا دوباره تلاش کنید.');
        },
        complete: function() {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'ثبت';
            }
        }
    });
}


function handleSubmitResponse(response) {
    if (response.success) {
        Swal.fire({
            title: 'موفقیت',
            text: 'اطلاعات با موفقیت ثبت شد',
            icon: 'success',
            confirmButtonText: 'باشه'
        }).then(() => {
            window.location.href = '/leave_reports/shift_report_list/';
        });
    } else {
         handleSubmitError(response.details || response.error || 'خطا در ثبت اطلاعات');
    }
}


function handleSubmitError(error) {
    let message = 'خطا در ثبت اطلاعات';
     if (typeof error === 'string') {
        message = error;
    } else if (Array.isArray(error)) {
        message = error.join('<br>');
    }
      Swal.fire({
        title: 'خطا',
        html: message,
        icon: 'error',
        confirmButtonText: 'باشه',
         customClass: {
            container: 'rtl-alert',
            popup: 'rtl-alert',
            title: 'rtl-alert',
            confirmButton: 'rtl-alert btn btn-primary'
        }
    });
}

function showError(message) {
    Swal.fire({
        title: 'خطا',
        text: message,
        icon: 'error',
        confirmButtonText: 'باشه',
        customClass: {
            container: 'rtl-alert',
            popup: 'rtl-alert',
            title: 'rtl-alert',
            confirmButton: 'rtl-alert btn btn-primary'
        }
    });
}