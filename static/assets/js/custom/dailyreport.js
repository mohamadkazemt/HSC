// Enhanced JavaScript Functions for Managing Steps and Dynamic Content

document.addEventListener('DOMContentLoaded', function() {
    $('.form-select').select2();
    handleStepperNavigation();
});

// Stepper Navigation Logic
function handleStepperNavigation() {
    const stepper = document.getElementById('kt_create_account_stepper');
    const steps = stepper.querySelectorAll('[data-kt-stepper-element="content"]');
    let currentStepIndex = 0;

    function showStep(index) {
        steps.forEach((step, i) => {
            step.style.display = i === index ? 'block' : 'none';
        });
        document.querySelectorAll('[data-kt-stepper-action="previous"]').forEach(button => {
            button.style.display = index === 0 ? 'none' : 'inline-block';
        });
        document.querySelectorAll('[data-kt-stepper-action="next"]').forEach(button => {
            button.style.display = index === steps.length - 1 ? 'none' : 'inline-block';
        });
        document.querySelectorAll('[data-kt-stepper-action="submit"]').forEach(button => {
            button.style.display = index === steps.length - 1 ? 'inline-block' : 'none';
        });
    }

    function goToNextStep() {
        if (validateStep(currentStepIndex)) {
            if (currentStepIndex < steps.length - 1) {
                currentStepIndex++;
                showStep(currentStepIndex);
            }
        }
    }

    function goToPreviousStep() {
        if (currentStepIndex > 0) {
            currentStepIndex--;
            showStep(currentStepIndex);
        }
    }

    document.querySelectorAll('[data-kt-stepper-action="next"]').forEach(button => {
        button.addEventListener('click', goToNextStep);
    });

    document.querySelectorAll('[data-kt-stepper-action="previous"]').forEach(button => {
        button.addEventListener('click', goToPreviousStep);
    });

    showStep(currentStepIndex);
}

// Enhanced Validation Logic for Each Step
function validateStep(stepIndex) {
    const stepForms = document.querySelectorAll('[data-kt-stepper-element="content"]')[stepIndex];
    const inputs = stepForms.querySelectorAll('input, select, textarea');
    let isValid = true;

    inputs.forEach(input => {
        if (input.required && !input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });

    return isValid;
}

// Generic Function to Add Entries
function addEntry(formType) {
    const blockSelect = document.querySelector(`[name="${formType}_block"]`);
    const machineSelect = document.querySelector(`[name="${formType}_machine"]`);
    const statusSelect = document.querySelector(`[name="${formType}_status"]`);
    const descriptionInput = document.querySelector(`[name="${formType}_description"]`);
    const entryList = document.getElementById(`${formType}_list`);

    let description = descriptionInput ? descriptionInput.value.trim() : '';
    let blockText = blockSelect ? blockSelect.options[blockSelect.selectedIndex]?.text : '';
    let machineText = machineSelect ? machineSelect.options[machineSelect.selectedIndex]?.text : '';
    let statusText = statusSelect ? statusSelect.options[statusSelect.selectedIndex]?.text : '';

    // Validate Inputs
    if ((blockSelect && !blockSelect.value) ||
        (machineSelect && !machineSelect.value) ||
        (statusSelect && !statusSelect.value) ||
        (descriptionInput && !description)) {
        alert('لطفاً تمامی اطلاعات را تکمیل کنید.');
        return;
    }

    // Check for Duplicates
    const existingEntries = entryList.querySelectorAll('.alert');
    for (let entry of existingEntries) {
        if (entry.textContent.includes(blockText) &&
            (machineText === '' || entry.textContent.includes(machineText)) &&
            (statusText === '' || entry.textContent.includes(statusText)) &&
            (description === '' || entry.textContent.includes(description))) {
            alert('این مورد قبلاً اضافه شده است.');
            return;
        }
    }

    // Create New Entry
    const newEntry = document.createElement('div');
    newEntry.className = 'alert alert-secondary mt-3 d-flex justify-content-between align-items-center';
    newEntry.innerHTML = `
        <span>${blockText} ${machineText ? `- ${machineText}` : ''} ${statusText ? `- ${statusText}` : ''} ${description ? `- ${description}` : ''}</span>
        <button type="button" class="btn btn-danger btn-sm" onclick="removeEntry(this)">حذف</button>
    `;

    // Append Entry
    entryList.appendChild(newEntry);

    // Clear Inputs
    if (blockSelect) blockSelect.selectedIndex = 0;
    if (machineSelect) machineSelect.selectedIndex = 0;
    if (statusSelect) statusSelect.selectedIndex = 0;
    if (descriptionInput) descriptionInput.value = '';
}

// Remove an Entry
function removeEntry(button) {
    if (confirm('آیا مطمئن هستید که می‌خواهید این مورد را حذف کنید؟')) {
        button.parentElement.remove();
    }
}

// Toggle Visibility Functions
function toggleVisibility(statusId, detailsId) {
    const status = document.getElementById(statusId).value;
    const details = document.getElementById(detailsId);
    details.style.display = status === 'yes' ? 'block' : 'none';
}
