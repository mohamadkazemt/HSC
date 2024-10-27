document.addEventListener('DOMContentLoaded', function () {
    // پس از ارسال فرم، پاسخ را به صورت AJAX دریافت کنید
    const form = document.getElementById('kt_create_account_form');
    form.addEventListener('submit', function (event) {
        event.preventDefault(); // جلوگیری از ارسال فرم به صورت پیش‌فرض

        const formData = new FormData(form);
        fetch(form.action, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // بررسی و نمایش پیام‌ها با استفاده از SweetAlert
            if (data.messages && data.messages.length > 0) {
                data.messages.forEach(message => {
                    const messageType = message.tags.includes('success') ? 'success' : 'error';
                    Swal.fire({
                        title: messageType === 'success' ? 'موفقیت' : 'خطا',
                        text: message.message,
                        icon: messageType,
                        confirmButtonText: 'باشه'
                    });
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            Swal.fire({
                title: 'خطا',
                text: 'خطایی در ارتباط با سرور رخ داد.',
                icon: 'error',
                confirmButtonText: 'باشه'
            });
        });
    });
});



function addLoadingOperation() {
    const stoneType = document.getElementById("stone_type").value;
    const loadCount = document.getElementById("load_count").value;
    if (stoneType && loadCount) {
        const list = document.getElementById("loading_list");
        const entry = document.createElement('li');
        entry.className = "list-group-item d-flex justify-content-between align-items-center";
        entry.textContent = `نوع سنگ: ${stoneType}, تعداد بار: ${loadCount}`;
        const hiddenInput = document.createElement('input');
        hiddenInput.type = "hidden";
        hiddenInput.name = "loading_operations[]";
        hiddenInput.value = `${stoneType},${loadCount}`;
        document.getElementById("kt_create_account_form").appendChild(hiddenInput);
        const deleteButton = document.createElement('button');
        deleteButton.className = "btn btn-danger btn-sm";
        deleteButton.textContent = "حذف";
        deleteButton.onclick = function () {
            list.removeChild(entry);
            document.getElementById("kt_create_account_form").removeChild(hiddenInput);
        };
        entry.appendChild(deleteButton);
        list.appendChild(entry);
    } else {
        // نمایش خطا به صورت زیبا با استفاده از SweetAlert
        Swal.fire({
            title: 'خطا',
            text: 'لطفا نوع سنگ و تعداد بار را وارد کنید.',
            icon: 'error',
            confirmButtonText: 'باشه'
        });
    }
}

function addLeave() {
    const personnel = document.getElementById("personnel_name").value;
    const status = document.getElementById("leave_status").value;
    if (personnel && status) {
        const list = document.getElementById("leave_list");
        const entry = document.createElement('li');
        entry.className = "list-group-item d-flex justify-content-between align-items-center";
        entry.textContent = `پرسنل: ${personnel}, وضعیت مرخصی: ${status}`;
        const hiddenInput = document.createElement('input');
        hiddenInput.type = "hidden";
        hiddenInput.name = "leaves[]";
        hiddenInput.value = `${personnel},${status}`;
        document.getElementById("kt_create_account_form").appendChild(hiddenInput);
        const deleteButton = document.createElement('button');
        deleteButton.className = "btn btn-danger btn-sm";
        deleteButton.textContent = "حذف";
        deleteButton.onclick = function () {
            list.removeChild(entry);
            document.getElementById("kt_create_account_form").removeChild(hiddenInput);
        };
        entry.appendChild(deleteButton);
        list.appendChild(entry);
    } else {
        Swal.fire({
            title: 'خطا',
            text: 'لطفا پرسنل و وضعیت مرخصی را انتخاب کنید.',
            icon: 'error',
            confirmButtonText: 'باشه'
        });
    }
}

function addVehicle() {
    const vehicleId = document.getElementById("vehicle_name").value;
    const vehicleName = document.getElementById("vehicle_name").options[document.getElementById("vehicle_name").selectedIndex].text;
    if (vehicleId) {
        const list = document.getElementById("vehicle_list");
        const entry = document.createElement('li');
        entry.className = "list-group-item d-flex justify-content-between align-items-center";
        entry.textContent = `خودرو: ${vehicleName}`;
        const hiddenInput = document.createElement('input');
        hiddenInput.type = "hidden";
        hiddenInput.name = "vehicles[]";
        hiddenInput.value = `${vehicleId}`;
        document.getElementById("kt_create_account_form").appendChild(hiddenInput);
        const deleteButton = document.createElement('button');
        deleteButton.className = "btn btn-danger btn-sm";
        deleteButton.textContent = "حذف";
        deleteButton.onclick = function () {
            list.removeChild(entry);
            document.getElementById("kt_create_account_form").removeChild(hiddenInput);
        };
        entry.appendChild(deleteButton);
        list.appendChild(entry);
    } else {
        Swal.fire({
            title: 'خطا',
            text: 'لطفا نام خودرو را انتخاب کنید.',
            icon: 'error',
            confirmButtonText: 'باشه'
        });
    }
}

function nextStep() {
    const currentStep = document.querySelector(".stepper-item.current");
    const nextStep = currentStep.nextElementSibling;
    if (nextStep) {
        currentStep.classList.remove("current");
        nextStep.classList.add("current");
        const currentContent = document.querySelector("[data-kt-stepper-element='content'].current");
        const nextContent = currentContent.nextElementSibling;
        if (nextContent) {
            currentContent.classList.remove("current");
            nextContent.classList.add("current");
        }
    }
}

function previousStep() {
    const currentStep = document.querySelector(".stepper-item.current");
    const previousStep = currentStep.previousElementSibling;
    if (previousStep) {
        currentStep.classList.remove("current");
        previousStep.classList.add("current");
        const currentContent = document.querySelector("[data-kt-stepper-element='content'].current");
        const previousContent = currentContent.previousElementSibling;
        if (previousContent) {
            currentContent.classList.remove("current");
            previousContent.classList.add("current");
        }
    }
}
