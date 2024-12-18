document.addEventListener("DOMContentLoaded", function () {
    const steps = document.querySelectorAll("[data-kt-stepper-element='content']");
    const nextButtons = document.querySelectorAll("[data-kt-stepper-action='next']");
    const prevButtons = document.querySelectorAll("[data-kt-stepper-action='previous']");
    const submitButton = document.querySelector("[data-kt-stepper-action='submit']");
    let currentStep = 0;

    /** نمایش مراحل */
    function showStep(index) {
        steps.forEach((step, i) => {
            step.style.display = i === index ? "block" : "none";
        });
        prevButtons.forEach((btn) => btn.style.display = index === 0 ? "none" : "inline-block");
        nextButtons.forEach((btn) => btn.style.display = index === steps.length - 1 ? "none" : "inline-block");
        submitButton.style.display = index === steps.length - 1 ? "inline-block" : "none";
    }

    /** دکمه مرحله بعد و مرحله قبل */
    nextButtons.forEach(button => {
        button.addEventListener("click", () => {
            if (currentStep < steps.length - 1) currentStep++;
            showStep(currentStep);
        });
    });

    prevButtons.forEach(button => {
        button.addEventListener("click", () => {
            if (currentStep > 0) currentStep--;
            showStep(currentStep);
        });
    });

    showStep(currentStep);

    // **استفاده از select2**
    $('.select2').select2({
        placeholder: "لطفاً انتخاب کنید",
        allowClear: true
    });


    /** جزئیات آتشباری */
    document.getElementById("blasting_status").addEventListener("change", function () {
        const blastingDetails = document.getElementById("blasting_details");
        blastingDetails.style.display = this.value === "yes" ? "block" : "none";
    });

    window.addBlastingDetail = function () {
        // بررسی مجدد برای اطمینان از نمایش المان
        const blastingDetails = document.getElementById("blasting_details");
        if (blastingDetails.style.display !== "block") {
            alert("لطفاً ابتدا وضعیت آتشباری را روی 'بله' قرار دهید.");
            return;
        }

        // انتخاب مقادیر از فرم
        const explosionOccurred = document.getElementById("blasting_status").value;
        const explosionStatusText = explosionOccurred === "yes" ? "انفجار انجام شد" : "انفجار انجام نشد";
        const isExplosionStatus = explosionOccurred === "yes"; // مقدار بولی

        const blockSelect = document.getElementById("blasting_block");
        const blockId = blockSelect.value;  // مقدار عددی id
        const blockName = blockSelect.options[blockSelect.selectedIndex].text;

        const description = document.getElementById("blasting_description").value;

        if (!blockId || blockId === "انتخاب بلوک") {
            alert("لطفاً بلوک را انتخاب کنید.");
            return;
        }

        // اضافه کردن جزئیات به جدول
        const tableBody = document.querySelector('#blasting_table tbody');
        const row = document.createElement("tr");

        // اضافه کردن explosionStatus به عنوان یک مقدار مجزا (hidden attribute)
        row.innerHTML = `
        <td>${explosionStatusText}</td>
        <td data-value="${blockId}">${blockName}</td>
        <td>${description}</td>
        <td>
            <input type="hidden" name="is_explosion_status" value="${isExplosionStatus}">
            <button type="button" onclick="removeBlastingDetail(this)" class="btn btn-danger btn-sm">حذف</button>
        </td>
    `;
        tableBody.appendChild(row);

        // پاک کردن مقادیر فرم
        blockSelect.selectedIndex = 0;
        document.getElementById("blasting_description").value = "";
    };

        window.removeBlastingDetail = function (button) {
        const row = button.closest("tr");
        row.remove();1
    };




    /** جزئیات حفاری */
    window.addDrillingDetail = function () {
        const blockId = document.querySelector('[name="drilling_block"]').value;
        const machineId = document.querySelector('[name="drilling_machine"]').value;
        const status = document.querySelector('[name="drilling_status"]').value;

        if (!blockId || !machineId || !status) {
            alert("لطفاً تمام فیلدها را پر کنید.");
            return;
        }

        // پیدا کردن نام‌ها
        const blockName = miningBlocks.find(block => block.id === parseInt(blockId))?.block_name || "نامشخص";
        const machineName = miningMachines.find(machine => machine.id === parseInt(machineId))?.workshop_code || "نامشخص";

        // نمایش در جدول
        const tableBody = document.querySelector('#drilling_table tbody');
        const row = document.createElement("tr");

        row.innerHTML = `
        <td data-value="${blockId}">${blockName}</td>
        <td data-value="${machineId}">${machineName}</td>
        <td>${status}</td>
        <td>
            <button type="button" onclick="removeDrillingDetail(this)" class="btn btn-danger btn-sm">حذف</button>
        </td>
    `;

        tableBody.appendChild(row);
    };

    window.removeDrillingDetail = function (button) {
        const row = button.closest("tr");
        row.remove();
    };





    /** جزئیات بارگیری */
    window.addLoadingDetail = function () {
        const blockId = document.querySelector('[name="loading_block"]').value;
        const machineId = document.querySelector('[name="loading_machine"]').value;
        const status = document.querySelector('[name="loading_status"]').value;

        if (!blockId || !machineId || !status) {
            alert("لطفاً تمام فیلدها را پر کنید.");
            return;
        }

        // پیدا کردن نام بلوک و دستگاه از داده‌های موجود
        const blockName = miningBlocks.find(({id}) => id === parseInt(blockId))?.block_name || "نامشخص";
        const machineName = miningMachines.find(({id}) => id === parseInt(machineId))?.workshop_code || "نامشخص";

        // افزودن جزئیات به جدول
        const tableBody = document.querySelector('#loading_table tbody');
        const row = document.createElement("tr");

        row.innerHTML = `
        <td data-value="${blockId}">${blockName}</td>
        <td data-value="${machineId}">${machineName}</td>
        <td>${status}</td>
        <td>
            <button type="button" onclick="removeLoadingDetail(this)" class="btn btn-danger btn-sm">حذف</button>
        </td>
    `;
        tableBody.appendChild(row);
    };

// تابع حذف ردیف
    window.removeLoadingDetail = function (button) {
        const row = button.closest("tr");
        row.remove();
    };



    /** جزئیات تخلیه */
    window.addDumpDetail = function () {
        const dumpSelect = document.querySelector('[name="dump"]');
        const dumpId = dumpSelect.value;
        const dumpName = dumpSelect.options[dumpSelect.selectedIndex].text;
        const status = document.querySelector('[name="dump_status"]').value;
        const description = document.querySelector('[name="dump_description"]').value;
        console.log("Dump ID:", dumpId);
        console.log("Dump Name:", dumpName);


        if (!dumpId || dumpId === "انتخاب دامپ") {
            alert("لطفاً دامپ را انتخاب کنید.");
            return;
        }

        const tableBody = document.querySelector('#dump_table tbody');
        const row = document.createElement("tr");

        row.innerHTML = `
        <td data-value="${dumpId}">${dumpName}</td>
        <td>${status}</td>
        <td>${description}</td>
        <td>
            <button type="button" onclick="removeDumpDetail(this)" class="btn btn-danger btn-sm">حذف</button>
        </td>
    `;
        tableBody.appendChild(row);
    };


    window.removeDumpDetail = function (button) {
        const row = button.closest("tr");
        row.remove();
    };



    /** جزئیات بازرسی */
    document.getElementById("inspection_status").addEventListener("change", function () {
        const details = document.getElementById("inspection_details");
        details.style.display = this.value === "yes" ? "block" : "none";
    });

    window.addInspectionDetail = function () {
        const inspection = document.querySelector('[name="inspection"]').value;
        const status = document.querySelector('[name="inspection_status"]').value;
        const description = document.querySelector('[name="inspection_description"]').value;

        if (!inspection || !status) {
            alert("لطفاً تمام فیلدها را پر کنید.");
            return;
        }

        // تبدیل وضعیت به متن خوانا
        const statusText = status === "yes" ? "انجام شد" : "انجام نشد";

        // اضافه کردن جزئیات به جدول
        const tableBody = document.querySelector('#inspection_table tbody');
        const row = document.createElement("tr");

        row.innerHTML = `
        <td>${inspection}</td>
        <td>${statusText}</td>
        <td>${description}</td>
        <td>
            <button type="button" onclick="removeInspectionDetail(this)" class="btn btn-danger btn-sm">حذف</button>
        </td>
    `;
        tableBody.appendChild(row);

        // پاک کردن مقادیر فرم
        document.querySelector('[name="inspection"]').value = "";
        document.querySelector('[name="inspection_description"]').value = "";
    };

// تابع حذف ردیف
    window.removeInspectionDetail = function (button) {
        const row = button.closest("tr");
        row.remove();
    };



    /** توقفات */
    window.addStoppageDetail = function () {
        const reason = document.querySelector('[name="stoppage_reason"]').value;
        const start = document.querySelector('[name="stoppage_start"]').value;
        const end = document.querySelector('[name="stoppage_end"]').value;

        if (!reason || !start || !end) {
            alert("لطفاً تمام فیلدها را پر کنید.");
            return;
        }

        const tableBody = document.querySelector('#stoppage_table tbody');
        const row = document.createElement("tr");

        row.innerHTML = `
        <td>${reason}</td>
        <td>${start}</td>
        <td>${end}</td>
        <td>
            <button type="button" onclick="removeStoppageDetail(this)" class="btn btn-danger btn-sm">حذف</button>
        </td>
    `;
        tableBody.appendChild(row);
    };

    window.removeStoppageDetail = function (button) {
        const row = button.closest("tr");
        row.remove();
    };


    /** پیگیری */
    window.addFollowupDetail = function () {
        const description = document.querySelector('[name="followup_description"]').value;
        const files = document.querySelector('[name="followup_files"]').files;

        if (!description) {
            alert("لطفاً توضیحات را وارد کنید.");
            return;
        }

        const tableBody = document.querySelector('#followup_table tbody');
        const row = document.createElement("tr");

        let fileNames = "";
        for (let i = 0; i < files.length; i++) {
            fileNames += `${files[i].name}, `;
        }

        row.innerHTML = `
        <td>${description}</td>
        <td>${fileNames || "بدون فایل"}</td>
        <td>
            <button type="button" onclick="removeFollowupDetail(this)" class="btn btn-danger btn-sm">حذف</button>
        </td>
    `;
        tableBody.appendChild(row);
    };

    window.removeFollowupDetail = function (button) {
        const row = button.closest("tr");
        row.remove();
    };

// لاگ کردن جزئیات آتشباری
    console.log("Blasting Details:", JSON.stringify(collectDetailsFromTable('#blasting_table', ['block_id', 'description'])));

// لاگ کردن جزئیات حفاری
    console.log("Drilling Details:", JSON.stringify(collectDetailsFromTable('#drilling_table', ['block_id', 'machine_id', 'status'])));

// لاگ کردن جزئیات بارگیری
    console.log("Loading Details:", JSON.stringify(collectDetailsFromTable('#loading_table', ['block_id', 'machine_id', 'status'])));

// لاگ کردن جزئیات تخلیه
    console.log("Dump Details:", JSON.stringify(collectDetailsFromTable('#dump_table', ['dump_id', 'status', 'description'])));

// لاگ کردن جزئیات بازرسی
    console.log("Inspection Details:", JSON.stringify(collectDetailsFromTable('#inspection_table', ['inspection', 'inspection_status', 'inspection_description'])));

// لاگ کردن جزئیات توقفات
    console.log("Stoppage Details:", JSON.stringify(collectDetailsFromTable('#stoppage_table', ['reason', 'start_time', 'end_time'])));

// لاگ کردن جزئیات پیگیری
    console.log("Followup Details:", JSON.stringify(collectDetailsFromTable('#followup_table', ['description', 'file_input_name'])));

    /** ارسال فرم */
    document.querySelector('[data-kt-stepper-action="submit"]').addEventListener("click", function (e) {
        e.preventDefault();

        // جمع‌آوری جزئیات از جدول‌ها
        const blastingDetails = collectDetailsFromTable('#blasting_table', ['block_id', 'description']);
        const drillingDetails = collectDetailsFromTable('#drilling_table', ['block_id', 'machine_id', 'status']);
        const loadingDetails = collectDetailsFromTable('#loading_table', ['block_id', 'machine_id', 'status']);
        const dumpDetails = collectDetailsFromTable('#dump_table', ['dump_id', 'status', 'description']);
        const stoppageDetails = collectDetailsFromTable('#stoppage_table', ['reason', 'start_time', 'end_time']);
        const followupDetails = collectDetailsFromTable('#followup_table', ['description', 'file_input_name']);

        // ایجاد hidden inputs برای جزئیات
        addHiddenInputToForm("blasting_details", JSON.stringify(blastingDetails));
        addHiddenInputToForm("drilling_details", JSON.stringify(drillingDetails));
        addHiddenInputToForm("loading_details", JSON.stringify(loadingDetails));
        addHiddenInputToForm("dump_details", JSON.stringify(dumpDetails));
        addHiddenInputToForm("stoppage_details", JSON.stringify(stoppageDetails));
        addHiddenInputToForm("followup_details", JSON.stringify(followupDetails));

        // ارسال فرم
        document.querySelector("#kt_create_account_form").submit();
    });

// توابع کمکی برای جمع‌آوری جزئیات
    function collectDetailsFromTable(tableId, fields) {
        const rows = document.querySelectorAll(`${tableId} tbody tr`);
        const details = [];
        rows.forEach(row => {
            const detail = {};
            fields.forEach((field, index) => {
                const cell = row.children[index];
                if (field === 'block_id' || field === 'dump_id') {
                    detail[field] = cell.dataset.value; // دریافت block_id
                } else if (field === 'is_explosion_status') {
                    detail[field] = row.querySelector('input[name="is_explosion_status"]').value;
                } else {
                    detail[field] = cell.innerText.trim();
                }
            });
            details.push(detail);
        });
        return details;
    }


    function addHiddenInputToForm(name, value) {
        const hiddenInput = document.createElement("input");
        hiddenInput.type = "hidden";
        hiddenInput.name = name;
        hiddenInput.value = value;
        document.querySelector("#kt_create_account_form").appendChild(hiddenInput);
    }
});

