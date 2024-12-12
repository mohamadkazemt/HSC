
// JavaScript Functions for Managing Steps and Dynamic Content

// Initialize Select2 for dynamic dropdowns
document.addEventListener('DOMContentLoaded', function() {
    $('.form-select').select2();

    // Initialize step navigation
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

// Validation Logic for Each Step
function validateStep(stepIndex) {
    // Add custom validation logic for each step if needed
    // Example: return false if validation fails for the step
    return true; // Assuming all steps are valid for now
}

// Toggle Blasting Details
function toggleBlastingDetails() {
    const blastingStatus = document.getElementById('blasting_status').value;
    const blastingDetails = document.getElementById('blasting_details');
    if (blastingStatus === 'yes') {
        blastingDetails.style.display = 'block';
    } else {
        blastingDetails.style.display = 'none';
    }
}

// Add a new blasting entry
function addBlasting() {
    const blockSelect = document.querySelector('[name="blasting_block"]');
    const description = document.querySelector('[name="blasting_description"]').value;
    const blastingList = document.getElementById('blasting_list');

    if (blockSelect.value && description) {
        const newEntry = document.createElement('div');
        newEntry.className = 'alert alert-secondary mt-3 d-flex justify-content-between';
        newEntry.innerHTML = `${blockSelect.options[blockSelect.selectedIndex].text} - ${description}
                              <button type="button" class="btn btn-danger btn-sm" onclick="removeEntry(this)">حذف</button>`;
        blastingList.appendChild(newEntry);
        blockSelect.selectedIndex = 0;
        document.querySelector('[name="blasting_description"]').value = '';
    } else {
        alert('لطفاً تمامی اطلاعات را تکمیل کنید.');
    }
}

// Toggle Inspection Details
function toggleInspection() {
    const inspectionStatus = document.getElementById('inspection_status').value;
    const inspectionDetails = document.getElementById('inspection_status_detail');
    if (inspectionStatus === 'yes') {
        inspectionDetails.style.display = 'block';
    } else {
        inspectionDetails.style.display = 'none';
    }
}

// Toggle Stop Details
function toggleStop() {
    const stopStatus = document.getElementById('stoppage_status').value;
    const stopDetails = document.getElementById('stoppage_details');
    if (stopStatus === 'yes') {
        stopDetails.style.display = 'block';
    } else {
        stopDetails.style.display = 'none';
    }
}

// Add a new drilling entry
function addDrilling() {
    const blockSelect = document.querySelector('[name="drilling_block"]');
    const machineSelect = document.querySelector('[name="drilling_machine"]');
    const statusSelect = document.querySelector('[name="drilling_status"]');
    const drillingList = document.getElementById('drilling_list');

    if (blockSelect.value && machineSelect.value && statusSelect.value) {
        const newEntry = document.createElement('div');
        newEntry.className = 'alert alert-secondary mt-3 d-flex justify-content-between';
        newEntry.innerHTML = `${blockSelect.options[blockSelect.selectedIndex].text} -
                              ${machineSelect.options[machineSelect.selectedIndex].text} -
                              ${statusSelect.options[statusSelect.selectedIndex].text}
                              <button type="button" class="btn btn-danger btn-sm" onclick="removeEntry(this)">حذف</button>`;
        drillingList.appendChild(newEntry);
        blockSelect.selectedIndex = 0;
        machineSelect.selectedIndex = 0;
        statusSelect.selectedIndex = 0;
    } else {
        alert('لطفاً تمامی اطلاعات را تکمیل کنید.');
    }
}

// Add a new dump entry
function addDump() {
    const dumpSelect = document.querySelector('[name="dump_block"]');
    const statusSelect = document.querySelector('[name="dump_status"]');
    const description = document.querySelector('[name="dump_description"]').value;
    const dumpList = document.getElementById('dump_list');

    if (dumpSelect.value && statusSelect.value && description) {
        const newEntry = document.createElement('div');
        newEntry.className = 'alert alert-secondary mt-3 d-flex justify-content-between';
        newEntry.innerHTML = `${dumpSelect.options[dumpSelect.selectedIndex].text} -
                              ${statusSelect.options[statusSelect.selectedIndex].text} -
                              ${description}
                              <button type="button" class="btn btn-danger btn-sm" onclick="removeEntry(this)">حذف</button>`;
        dumpList.appendChild(newEntry);
        dumpSelect.selectedIndex = 0;
        statusSelect.selectedIndex = 0;
        document.querySelector('[name="dump_description"]').value = '';
    } else {
        alert('لطفاً تمامی اطلاعات را تکمیل کنید.');
    }
}

// Add a new loading entry
function addLoading() {
    const blockSelect = document.querySelector('[name="loading_block"]');
    const machineSelect = document.querySelector('[name="loading_machine"]');
    const statusSelect = document.querySelector('[name="loading_status"]');
    const loadingList = document.getElementById('loading_list');

    if (blockSelect.value && machineSelect.value && statusSelect.value) {
        const newEntry = document.createElement('div');
        newEntry.className = 'alert alert-secondary mt-3 d-flex justify-content-between';
        newEntry.innerHTML = `${blockSelect.options[blockSelect.selectedIndex].text} -
                              ${machineSelect.options[machineSelect.selectedIndex].text} -
                              ${statusSelect.options[statusSelect.selectedIndex].text}
                              <button type="button" class="btn btn-danger btn-sm" onclick="removeEntry(this)">حذف</button>`;
        loadingList.appendChild(newEntry);
        blockSelect.selectedIndex = 0;
        machineSelect.selectedIndex = 0;
        statusSelect.selectedIndex = 0;
    } else {
        alert('لطفاً تمامی اطلاعات را تکمیل کنید.');
    }
}

// Remove an entry
function removeEntry(button) {
    button.parentElement.remove();
}


