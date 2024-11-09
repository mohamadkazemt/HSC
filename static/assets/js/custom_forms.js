let stepper;

document.addEventListener('DOMContentLoaded', function() {
    initializeStepper();
    initializeFormHandlers();
    initializeSelect2();
    initializeFileUpload();
    initializeMachineStatusHandler();

    setTimeout(() => {
        updateStepContent(1);
    }, 100);
});

function initializeStepper() {
    const stepperElement = document.querySelector("#kt_create_account_stepper");
    if (!stepperElement) return;
    stepper = new KTStepper(stepperElement);

    document.querySelectorAll('[data-kt-stepper-action="next"]').forEach(btn =>
        btn.addEventListener('click', handleNextStep));

    document.querySelectorAll('[data-kt-stepper-action="previous"]').forEach(btn =>
        btn.addEventListener('click', handlePreviousStep));
}

function initializeFormHandlers() {
    const form = document.getElementById('kt_create_account_form');
    if (!form) return;

    // Form submit handler
    form.addEventListener('submit', function(e) {
        e.preventDefault();
    });

    // Submit button click handler
    const submitBtn = document.querySelector('[data-kt-stepper-action="submit"]');
    if (submitBtn) {
        submitBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const form = document.getElementById('kt_create_account_form');
            if (form && validateAllSteps()) {
                submitShiftReport(form);
            }
        });
    }
}

function initializeSelect2() {
    $('.select2').select2({
        dir: "rtl",
        width: '100%',
        language: {
            noResults: () => "نتیجه‌ای یافت نشد",
            searching: () => "در حال جستجو..."
        },
        dropdownParent: $('#kt_create_account_stepper'),
        selectionCssClass: 'form-select form-select-solid',
        dropdownCssClass: 'select2-dropdown-kt',
        placeholder: 'انتخاب کنید...'
    }).on('select2:open', function() {
        setTimeout(function() {
            $('.select2-search__field').addClass('form-control form-control-solid');
            $('.select2-dropdown').addClass('select2-dropdown-kt');
        }, 0);
    });
}

function initializeFileUpload() {
    const fileInput = document.querySelector('input[type="file"]');
    if (!fileInput) return;

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file && !validateFile(file)) {
            e.target.value = '';
        }
    });
}

function initializeMachineStatusHandler() {
    const machineStatus = document.getElementById('machine_status');
    machineStatus?.addEventListener('change', function() {
        const reasonContainer = document.querySelector('.machine-inactive-reason');
        if (reasonContainer) {
            reasonContainer.style.display = this.value === 'inactive' ? 'block' : 'none';
        }
    });
}

function getTotalSteps() {
    return document.querySelectorAll('[data-kt-stepper-element="content"]').length;
}

function handleNextStep() {
    if (validateCurrentStep(stepper.getCurrentStepIndex())) {
        stepper.goNext();
        updateStepContent(stepper.getCurrentStepIndex());
    }
}

function handlePreviousStep() {
    stepper.goPrevious();
    updateStepContent(stepper.getCurrentStepIndex());
}

function updateStepContent(stepIndex) {
    document.querySelectorAll('[data-kt-stepper-element="content"]')
        .forEach(content => {
            content.style.display = 'none';
            content.classList.remove('current');
        });

    const currentContent = document.querySelectorAll('[data-kt-stepper-element="content"]')[stepIndex - 1];
    if (currentContent) {
        currentContent.style.display = 'block';
        currentContent.classList.add('current');
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
    if (submitBtn) {
        submitBtn.style.display = stepIndex === totalSteps ? 'block' : 'none';
        if (stepIndex === totalSteps) {
            setTimeout(() => submitBtn.style.display = 'block', 100);
        }
    }
}

// Validation Functions
function validateAllSteps() {
    const totalSteps = getTotalSteps();
    for (let i = 1; i <= totalSteps; i++) {
        if (!validateStep(i)) {
            stepper.goTo(i);
            return false;
        }
    }
    return true;
}

function validateStep(stepNumber) {
    const validationFunctions = {
        1: validateLoadingOperations,
        2: validateMiningMachines,
        3: validateLeaves,
        4: validateVehicles,
        5: validateSupervisorComments
    };

    return validationFunctions[stepNumber]?.() ?? true;
}

function validateCurrentStep(stepIndex) {
    return validateStep(stepIndex);
}

function validateLoadingOperations() {
    const tbody = document.querySelector('#loading_operations_table tbody');
    if (!tbody?.children.length) {
        showError('لطفا حداقل یک عملیات بارگیری را اضافه کنید');
        return false;
    }
    return true;
}

function validateMiningMachines() {
    const tbody = document.querySelector('#mining_machines_table tbody');
    if (!tbody?.children.length) {
        showError('لطفا حداقل یک ماشین‌آلات را اضافه کنید');
        return false;
    }
    return true;
}

function validateLeaves() {
    const tbody = document.querySelector('#leaves_table tbody');
    if (!tbody?.children.length) {
        showError('لطفا حداقل یک مرخصی را اضافه کنید');
        return false;
    }
    return true;
}

function validateVehicles() {
    const tbody = document.querySelector('#vehicles_table tbody');
    if (!tbody?.children.length) {
        showError('لطفا حداقل یک خودرو را اضافه کنید');
        return false;
    }
    return true;
}

function validateSupervisorComments() {
    const commentsTextarea = document.querySelector('[name="supervisor_comments"]');
    if (!commentsTextarea?.value.trim()) {
        showError('لطفا توضیحات سرشیفت را وارد کنید');
        return false;
    }
    return true;
}

function validateSelect2Fields() {
    let isValid = true;
    $('.select2[required]').each(function() {
        if (!$(this).val()) {
            const fieldName = $(this).data('placeholder') || 'این فیلد';
            showError(`لطفاً ${fieldName} را انتخاب کنید`);
            isValid = false;
            return false;
        }
    });
    return isValid;
}

function validateFile(file) {
    if (!file) return true;

    const maxSize = 5 * 1024 * 1024;
    if (file.size > maxSize) {
        showError('حجم فایل نباید بیشتر از 5 مگابایت باشد');
        return false;
    }

    const allowedTypes = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png'];
    const fileExtension = '.' + file.name.toLowerCase().split('.').pop();
    if (!allowedTypes.includes(fileExtension)) {
        showError('فرمت فایل مجاز نیست. فرمت‌های مجاز: PDF, Word, JPG');
        return false;
    }

    return true;
}

// Add Item Functions
function addLoadingOperation() {
    const stoneType = $('#stone_type');
    const loadCount = $('#load_count');

    if (!stoneType.val() || !loadCount.val()) {
        showError('لطفا نوع سنگ و تعداد بار را وارد کنید');
        return;
    }

    const loadCountValue = parseInt(loadCount.val());
    if (isNaN(loadCountValue) || loadCountValue <= 0) {
        showError('لطفا تعداد بار معتبر وارد کنید');
        return;
    }

    const tbody = document.querySelector('#loading_operations_table tbody');
    if (!tbody) {
        showError('جدول عملیات بارگیری یافت نشد');
        return;
    }

    try {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${stoneType.find('option:selected').text()}</td>
            <td>${loadCountValue}</td>
            <td>
                <button type="button" class="btn btn-sm btn-danger" onclick="removeTableRow(this)">حذف</button>
                <input type="hidden" name="loading_operations[]" value="${stoneType.val()},${loadCountValue}">
            </td>
        `;
        tbody.appendChild(tr);

        // Reset fields
        stoneType.val(null).trigger('change');
        loadCount.val('');

    } catch (error) {
        console.error('Error in addLoadingOperation:', error);
        showError('خطا در افزودن عملیات بارگیری');
    }
}
function addMiningMachine() {
    const machineSelect = $('#mining_machine_id');
    const blockSelect = $('#mining_block_id');
    const status = $('#machine_status');
    const inactiveReason = $('#machine_inactive_reason');

    if (!machineSelect.val() || !blockSelect.val()) {
        showError('لطفا ماشین‌آلات و بلوک را انتخاب کنید');
        return;
    }

    if (status.val() === 'inactive' && !inactiveReason.val()?.trim()) {
        showError('لطفا دلیل غیرفعال بودن را وارد کنید');
        return;
    }

    const tbody = document.querySelector('#mining_machines_table tbody');
    if (!tbody) {
        showError('جدول ماشین‌آلات یافت نشد');
        return;
    }

    try {
        const tr = document.createElement('tr');
        const machineText = machineSelect.find('option:selected').text();
        const blockText = blockSelect.find('option:selected').text();

        const [machineName, contractorName = '-'] = machineText.split(' - ');
        const [blockName, blockType = '-'] = blockText.split(' - ');

        tr.innerHTML = `
            <td>${machineName}</td>
            <td>${contractorName}</td>
            <td>${blockName}</td>
            <td>${blockType}</td>
            <td>${status.val() === 'active' ? 'فعال' : 'غیرفعال'}</td>
            <td>${inactiveReason.val() || '-'}</td>
            <td>
                <button type="button" class="btn btn-sm btn-danger" onclick="removeTableRow(this)">حذف</button>
                <input type="hidden" name="loader_statuses[]" value="${machineSelect.val()},${blockSelect.val()},${status.val()},${inactiveReason.val() || ''}">
            </td>
        `;
        tbody.appendChild(tr);

        // Reset fields
        machineSelect.val(null).trigger('change');
        blockSelect.val(null).trigger('change');
        status.val('active');
        inactiveReason.val('');
        $('.machine-inactive-reason').hide();

    } catch (error) {
        console.error('Error in addMiningMachine:', error);
        showError('خطا در افزودن ماشین‌آلات');
    }
}

function addLeave() {
    const personnelSelect = $('#personnel_id');
    const leaveStatus = $('#leave_status');

    if (!personnelSelect.val()) {
        showError('لطفا پرسنل را انتخاب کنید');
        return;
    }

    const tbody = document.querySelector('#leaves_table tbody');
    if (!tbody) {
        showError('جدول مرخصی‌ها یافت نشد');
        return;
    }

    try {
        const tr = document.createElement('tr');
        const personnelText = personnelSelect.find('option:selected').text();
        const [personnelName, personnelCode = '-'] = personnelText.split(' - ');

        tr.innerHTML = `
            <td>${personnelName}</td>
            <td>${personnelCode}</td>
            <td>${leaveStatus.val() === 'authorized' ? 'مجاز' : 'غیر مجاز'}</td>
            <td>
                <button type="button" class="btn btn-sm btn-danger" onclick="removeTableRow(this)">حذف</button>
                <input type="hidden" name="leaves[]" value="${personnelSelect.val()},${leaveStatus.val()}">
            </td>
        `;
        tbody.appendChild(tr);

        // Reset fields
        personnelSelect.val(null).trigger('change');
        leaveStatus.val('unauthorized');

    } catch (error) {
        console.error('Error in addLeave:', error);
        showError('خطا در افزودن مرخصی');
    }
}

function addVehicle() {
    const vehicleSelect = $('#vehicle_id');

    if (!vehicleSelect.val()) {
        showError('لطفا خودرو را انتخاب کنید');
        return;
    }

    const tbody = document.querySelector('#vehicles_table tbody');
    if (!tbody) {
        showError('جدول خودروها یافت نشد');
        return;
    }

    try {
        const tr = document.createElement('tr');
        const vehicleText = vehicleSelect.find('option:selected').text();
        const [vehicleName, contractorName = '-', vehicleType = '-'] = vehicleText.split(' - ');

        tr.innerHTML = `
            <td>${vehicleName}</td>
            <td>${contractorName}</td>
            <td>${vehicleType}</td>
            <td>
                <button type="button" class="btn btn-sm btn-danger" onclick="removeTableRow(this)">حذف</button>
                <input type="hidden" name="vehicles[]" value="${vehicleSelect.val()}">
            </td>
        `;
        tbody.appendChild(tr);

        // Reset fields
        vehicleSelect.val(null).trigger('change');

    } catch (error) {
        console.error('Error in addVehicle:', error);
        showError('خطا در افزودن خودرو');
    }
}

function removeTableRow(button) {
    try {
        button.closest('tr')?.remove();
    } catch (error) {
        console.error('Error in removeTableRow:', error);
        showError('خطا در حذف سطر');
    }
}

function submitShiftReport(formElement) {
    if (!validateAllSteps()) {
        return false;
    }

    // Validate supervisor comments
    const comments = $('[name="supervisor_comments"]');
    if (!comments.val()?.trim()) {
        showError('لطفا توضیحات سرشیفت را وارد کنید');
        return false;
    }

    const formData = new FormData(formElement);
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const submitBtn = document.querySelector('[data-kt-stepper-action="submit"]');

    // Add loading state
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> در حال ارسال...';
    }

    // Add all form data
    formData.append('supervisor_comments', comments.val().trim());

    // Add file if exists
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput?.files[0]) {
        formData.append('attached_file', fileInput.files[0]);
    }

    // Collect data from all tables
    const tables = {
        loading_operations: '#loading_operations_table',
        loader_statuses: '#mining_machines_table',
        leaves: '#leaves_table',
        vehicles: '#vehicles_table'
    };

    Object.entries(tables).forEach(([key, selector]) => {
        const data = [];
        document.querySelectorAll(`${selector} tbody tr input[type="hidden"]`).forEach(input => {
            data.push(input.value);
        });
        formData.append(key, JSON.stringify(data));
    });

    // Send AJAX request with jQuery
    $.ajax({
        url: formElement.action || window.location.href,
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        headers: { 'X-CSRFToken': csrftoken },
        success: handleSubmitResponse,
        error: handleSubmitError,
        complete: function() {
            // Reset submit button
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'ثبت گزارش';
            }
        }
    });
}

function handleSubmitResponse(response) {
    if (response.messages?.[0]) {
        const message = response.messages[0];
        Swal.fire({
            title: message.tags === 'success' ? 'موفقیت' : 'خطا',
            text: message.message,
            icon: message.tags === 'success' ? 'success' : 'error',
            confirmButtonText: 'باشه',
            customClass: getSwalCustomClasses()
        }).then(result => {
            if (result.isConfirmed && message.tags === 'success') {
                window.location.reload();
            }
        });
    }
}

function handleSubmitError(xhr) {
    let errorMessage = 'خطا در ارسال اطلاعات. لطفا دوباره تلاش کنید.';
    if (xhr.responseJSON?.messages?.[0]?.message) {
        errorMessage = xhr.responseJSON.messages[0].message;
    }

    Swal.fire({
        title: 'خطا',
        text: errorMessage,
        icon: 'error',
        confirmButtonText: 'باشه',
        customClass: getSwalCustomClasses()
    });
}

function showError(message) {
    Swal.fire({
        title: 'خطا',
        text: message,
        icon: 'error',
        confirmButtonText: 'باشه',
        customClass: getSwalCustomClasses()
    });
}

function getSwalCustomClasses() {
    return {
        container: 'rtl-alert',
        popup: 'rtl-alert',
        header: 'rtl-alert',
        title: 'rtl-alert',
        closeButton: 'rtl-alert',
        icon: 'rtl-alert',
        image: 'rtl-alert',
        content: 'rtl-alert',
        input: 'rtl-alert',
        actions: 'rtl-alert',
        confirmButton: 'rtl-alert btn btn-primary',
        cancelButton: 'rtl-alert btn btn-secondary',
        footer: 'rtl-alert'
    };
}