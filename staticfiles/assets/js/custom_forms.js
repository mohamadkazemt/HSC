document.addEventListener("DOMContentLoaded", function () {
    const steps = document.querySelectorAll("[data-kt-stepper-element='content']");
    const nextButtons = document.querySelectorAll("[data-kt-stepper-action='next']");
    const prevButtons = document.querySelectorAll("[data-kt-stepper-action='previous']");
    let currentStepIndex = 0;

    // نمایش مرحله خاص
    function showStep(index) {
        steps.forEach((step, i) => {
            step.style.display = i === index ? "block" : "none";
        });
    }

    // انتقال به مرحله بعد
    nextButtons.forEach((button) => {
        button.addEventListener("click", function () {
            if (currentStepIndex < steps.length - 1) {
                currentStepIndex++;
                showStep(currentStepIndex);
            }
        });
    });

    // بازگشت به مرحله قبل
    prevButtons.forEach((button) => {
        button.addEventListener("click", function () {
            if (currentStepIndex > 0) {
                currentStepIndex--;
                showStep(currentStepIndex);
            }
        });
    });

    // نمایش مرحله اول هنگام بارگذاری صفحه
    showStep(currentStepIndex);

    // تعامل با فرم مرحله آتشباری
    const blastingStatus = document.getElementById("blasting_status");
    const blastingDetails = document.getElementById("blasting_details");

    if (blastingStatus && blastingDetails) {
        blastingStatus.addEventListener("change", function () {
            if (blastingStatus.value === "yes") {
                blastingDetails.style.display = "block";
            } else {
                blastingDetails.style.display = "none";
            }
        });
    }

    // تعامل با فرم مرحله تعمیرگاه
    const inspectionStatus = document.getElementById("inspection_status");
    const inspectionDetails = document.getElementById("inspection_status_detail");

    if (inspectionStatus && inspectionDetails) {
        inspectionStatus.addEventListener("change", function () {
            if (inspectionStatus.value === "yes") {
                inspectionDetails.style.display = "block";
            } else {
                inspectionDetails.style.display = "none";
            }
        });
    }

    // تعامل با فرم مرحله توقفات
    const stoppageStatus = document.getElementById("stoppage_status");
    const stoppageDetails = document.getElementById("stoppage_details");

    if (stoppageStatus && stoppageDetails) {
        stoppageStatus.addEventListener("change", function () {
            if (stoppageStatus.value === "yes") {
                stoppageDetails.style.display = "block";
            } else {
                stoppageDetails.style.display = "none";
            }
        });
    }
});


// مدیریت مرحله اول: آتشباری
function addBlastingDetail() {
    const block = document.querySelector('[name="blasting_block"]').value;
    const status = document.querySelector('[name="blasting_status"]').checked ? 'بله' : 'خیر';
    const description = document.querySelector('[name="blasting_description"]').value;

    // بررسی خالی نبودن فیلدها
    if (!block || !description) {
        alert('لطفاً همه فیلدها را پر کنید.');
        return;
    }

    // اضافه کردن آیتم به لیست
    const blastingList = document.getElementById('blasting_items');
    const listItem = document.createElement('li');
    listItem.textContent = `بلوک: ${block} | وضعیت: ${status} | توضیحات: ${description}`;
    blastingList.appendChild(listItem);

    // ریست کردن فرم
    document.querySelector('[name="blasting_block"]').value = '';
    document.querySelector('[name="blasting_status"]').checked = false;
    document.querySelector('[name="blasting_description"]').value = '';
}

// مدیریت مرحله دوم: حفاری
function addDrillingDetail() {
    const block = document.querySelector('[name="drilling_block"]').value;
    const machine = document.querySelector('[name="drilling_machine"]').value;
    const status = document.querySelector('[name="drilling_status"]').value;
    const description = document.querySelector('[name="drilling_description"]').value;

    if (!block || !machine || !description) {
        alert('لطفاً همه فیلدها را پر کنید.');
        return;
    }

    const drillingList = document.getElementById('drilling_items');
    const listItem = document.createElement('li');
    listItem.textContent = `بلوک: ${block} | دستگاه: ${machine} | وضعیت: ${status} | توضیحات: ${description}`;
    drillingList.appendChild(listItem);

    document.querySelector('[name="drilling_block"]').value = '';
    document.querySelector('[name="drilling_machine"]').value = '';
    document.querySelector('[name="drilling_status"]').value = '';
    document.querySelector('[name="drilling_description"]').value = '';
}

// مدیریت مرحله سوم: دامپ‌ها
function addDumpDetail() {
    const dump = document.querySelector('[name="dump"]').value;
    const status = document.querySelector('[name="dump_status"]').value;
    const description = document.querySelector('[name="dump_description"]').value;

    if (!dump || !description) {
        alert('لطفاً همه فیلدها را پر کنید.');
        return;
    }

    const dumpList = document.getElementById('dump_items');
    const listItem = document.createElement('li');
    listItem.textContent = `دامپ: ${dump} | وضعیت: ${status} | توضیحات: ${description}`;
    dumpList.appendChild(listItem);

    document.querySelector('[name="dump"]').value = '';
    document.querySelector('[name="dump_status"]').value = '';
    document.querySelector('[name="dump_description"]').value = '';
}

// مدیریت مرحله چهارم: بارگیری
function addLoadingDetail() {
    const block = document.querySelector('[name="loading_block"]').value;
    const machine = document.querySelector('[name="loading_machine"]').value;
    const status = document.querySelector('[name="loading_status"]').value;
    const description = document.querySelector('[name="loading_description"]').value;

    if (!block || !machine || !description) {
        alert('لطفاً همه فیلدها را پر کنید.');
        return;
    }

    const loadingList = document.getElementById('loading_items');
    const listItem = document.createElement('li');
    listItem.textContent = `بلوک: ${block} | دستگاه: ${machine} | وضعیت: ${status} | توضیحات: ${description}`;
    loadingList.appendChild(listItem);

    document.querySelector('[name="loading_block"]').value = '';
    document.querySelector('[name="loading_machine"]').value = '';
    document.querySelector('[name="loading_status"]').value = '';
    document.querySelector('[name="loading_description"]').value = '';
}
