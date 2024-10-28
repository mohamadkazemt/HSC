// راه‌اندازی اولیه Select2 برای همه select‌ها
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('kt_create_account_form');
    form.addEventListener('submit', function(event) {
        event.preventDefault();

        const formData = new FormData(form);
        fetch(form.action, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
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

    // راه‌اندازی Select2
    $('.personnel-select').select2({
        placeholder: "جستجو و انتخاب پرسنل...",
        allowClear: true,
        width: '100%',
        dir: "rtl",
        language: {
            noResults: function() {
                return "نتیجه‌ای یافت نشد";
            },
            searching: function() {
                return "در حال جستجو...";
            }
        }
    });

    $('.vehicle-select').select2({
        placeholder: "جستجو و انتخاب خودرو...",
        allowClear: true,
        width: '100%',
        dir: "rtl",
        language: {
            noResults: function() {
                return "نتیجه‌ای یافت نشد";
            },
            searching: function() {
                return "در حال جستجو...";
            }
        }
    });

    $('.contractor-select').select2({
        placeholder: "جستجو و انتخاب پیمانکار...",
        allowClear: true,
        width: '100%',
        dir: "rtl",
        language: {
            noResults: function() {
                return "نتیجه‌ای یافت نشد";
            },
            searching: function() {
                return "در حال جستجو...";
            }
        }
    });

    // راه‌اندازی اولیه دکمه‌های ناوبری
    updateNavigationButtons();
});

function addLoadingOperation() {
    const stoneType = document.getElementById("stone_type").value;
    const stoneTypeText = $("#stone_type option:selected").text();
    const loadCount = document.getElementById("load_count").value;
    
    if (stoneType && loadCount) {
        const list = document.getElementById("loading_list");
        const entry = document.createElement('li');
        entry.className = "list-group-item d-flex justify-content-between align-items-center";
        entry.textContent = `نوع سنگ: ${stoneTypeText}, تعداد بار: ${loadCount}`;
        
        const hiddenInput = document.createElement('input');
        hiddenInput.type = "hidden";
        hiddenInput.name = "loading_operations[]";
        hiddenInput.value = `${stoneType},${loadCount}`;
        document.getElementById("kt_create_account_form").appendChild(hiddenInput);
        
        const deleteButton = document.createElement('button');
        deleteButton.className = "btn btn-danger btn-sm";
        deleteButton.textContent = "حذف";
        deleteButton.onclick = function() {
            list.removeChild(entry);
            document.getElementById("kt_create_account_form").removeChild(hiddenInput);
        };
        
        entry.appendChild(deleteButton);
        list.appendChild(entry);

        // پاک کردن فیلدها
        $("#stone_type").val('').trigger('change');
        $("#load_count").val('');
    } else {
        Swal.fire({
            title: 'خطا',
            text: 'لطفا نوع سنگ و تعداد بار را وارد کنید.',
            icon: 'error',
            confirmButtonText: 'باشه'
        });
    }
}

function addLeave() {
    const personnelSelect = $('#personnel_name');
    const personnelId = personnelSelect.val();
    const personnelName = personnelSelect.find('option:selected').text();
    const status = document.getElementById("leave_status").value;
    const statusText = $("#leave_status option:selected").text();

    if (personnelId && status) {
        const list = document.getElementById("leave_list");
        const entry = document.createElement('li');
        entry.className = "list-group-item d-flex justify-content-between align-items-center";
        entry.textContent = `پرسنل: ${personnelName}, وضعیت مرخصی: ${statusText}`;
        
        const hiddenInput = document.createElement('input');
        hiddenInput.type = "hidden";
        hiddenInput.name = "leaves[]";
        hiddenInput.value = `${personnelId},${status}`;
        document.getElementById("kt_create_account_form").appendChild(hiddenInput);
        
        const deleteButton = document.createElement('button');
        deleteButton.className = "btn btn-danger btn-sm";
        deleteButton.textContent = "حذف";
        deleteButton.onclick = function() {
            list.removeChild(entry);
            document.getElementById("kt_create_account_form").removeChild(hiddenInput);
        };
        
        entry.appendChild(deleteButton);
        list.appendChild(entry);

        // پاک کردن فیلدها
        personnelSelect.val(null).trigger('change');
        $("#leave_status").val('');
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
    const vehicleSelect = $('#vehicle_name');
    const vehicleId = vehicleSelect.val();
    const vehicleName = vehicleSelect.find('option:selected').text();

    if (vehicleId) {
        const list = document.getElementById("vehicle_list");
        const entry = document.createElement('li');
        entry.className = "list-group-item d-flex justify-content-between align-items-center";
        entry.textContent = `خودرو: ${vehicleName}`;
        
        const hiddenInput = document.createElement('input');
        hiddenInput.type = "hidden";
        hiddenInput.name = "vehicles[]";
        hiddenInput.value = vehicleId;
        document.getElementById("kt_create_account_form").appendChild(hiddenInput);
        
        const deleteButton = document.createElement('button');
        deleteButton.className = "btn btn-danger btn-sm";
        deleteButton.textContent = "حذف";
        deleteButton.onclick = function() {
            list.removeChild(entry);
            document.getElementById("kt_create_account_form").removeChild(hiddenInput);
        };
        
        entry.appendChild(deleteButton);
        list.appendChild(entry);

        // پاک کردن فیلد
        vehicleSelect.val(null).trigger('change');
    } else {
        Swal.fire({
            title: 'خطا',
            text: 'لطفا خودرو را انتخاب کنید.',
            icon: 'error',
            confirmButtonText: 'باشه'
        });
    }
}

function updateNavigationButtons() {
    const currentStep = document.querySelector(".stepper-item.current");
    const stepNumber = Array.from(currentStep.parentElement.children).indexOf(currentStep) + 1;
    const totalSteps = document.querySelectorAll(".stepper-item").length;
    
    const prevButton = document.getElementById("prevButton");
    const nextButton = document.getElementById("nextButton");
    const submitButton = document.getElementById("submitButton");
    
    if (stepNumber === 1) {
        prevButton.style.display = "none";
    } else {
        prevButton.style.display = "inline-flex";
    }
    
    if (stepNumber === totalSteps) {
        nextButton.style.display = "none";
        submitButton.style.display = "inline-flex";
    } else {
        nextButton.style.display = "inline-flex";
        submitButton.style.display = "none";
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
        updateNavigationButtons();
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
        updateNavigationButtons();
    }
}