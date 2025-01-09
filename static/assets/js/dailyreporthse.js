document.addEventListener("DOMContentLoaded", function () {
    function collectDetailsFromTable(tableId, fields) {
        const rows = document.querySelectorAll(`${tableId} tbody tr`);
        const details = [];
        rows.forEach(row => {
            const detail = {};
            fields.forEach((field, index) => {
                const cell = row.children[index];
                let value = cell.dataset.value || cell.innerText.trim();

                // تبدیل مقدار به عدد اگر فیلد مربوط به ID باشد
                if (field.endsWith("_id") && !isNaN(value)) {
                    value = parseInt(value, 10); // تبدیل رشته به عدد صحیح
                }

                // تبدیل مقدار به بولین اگر فیلد مربوط به بولین باشد
                if (field.endsWith("_occurred") || field === "inspection_done") {
                    value = value === "true" || value === "بله"; // تبدیل به true/false
                }
                 if (field === 'description') {
                        value = cell.dataset.description || cell.innerText.trim();
                    }


                detail[field] = value;
            });
            details.push(detail);
        });
        return details;
    }

    const steps = document.querySelectorAll("[data-kt-stepper-element='content']");
    const nextButtons = document.querySelectorAll("[data-kt-stepper-action='next']");
    const prevButtons = document.querySelectorAll("[data-kt-stepper-action='previous']");
    const submitButton = document.querySelector("[data-kt-stepper-action='submit']");
    let currentStep = 0;

    /** نمایش مراحل */
    function showStep(index) {
        console.log(`نمایش مرحله: ${index + 1}`);
        steps.forEach((step, i) => {
            step.style.display = i === index ? "block" : "none";
        });
        prevButtons.forEach((btn) => btn.style.display = index === 0 ? "none" : "inline-block");
        nextButtons.forEach((btn) => btn.style.display = index === steps.length - 1 ? "none" : "inline-block");
        submitButton.style.display = index === steps.length - 1 ? "inline-block" : "none";
    }

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

    $('.form-select-solid').select2({
        placeholder: "انتخاب کنید",
        allowClear: false,
        width: '100%', // عرض کامل
        dir: 'rtl', // جهت راست به چپ
        dropdownCssClass: 'form-select', // کلاس برای منوی دراپ‌داون
        containerCssClass: 'form-select' // کلاس برای کادر انتخاب
    });


    console.log("Select2 برای همه فیلدها فعال شد.");


    /** جمع‌آوری و افزودن داده‌ها */

// مرحله 1: جزئیات آتشباری
    document.getElementById("blasting_status").addEventListener("change", function () {
        const blastingDetails = document.getElementById("blasting_details");
        blastingDetails.style.display = this.value === "yes" ? "block" : "none";
        console.log(`وضعیت آتشباری تغییر کرد: ${this.value}`);
    });

    window.addBlastingDetail = function () {
        const blockSelect = document.getElementById("blasting_block");
        const blockId = blockSelect.value;

        if (!blockId || isNaN(blockId)) {
            alert("لطفاً یک بلوک معتبر انتخاب کنید.");
            return;
        }

        const blockName = blockSelect.options[blockSelect.selectedIndex].text;
        const description = document.getElementById("blasting_description").value;
        const explosionOccurred = document.getElementById("blasting_status").value === "yes";

        const tableBody = document.querySelector('#blasting_table tbody');
        const row = document.createElement("tr");

        row.innerHTML = `
        <td data-value="${blockId}">${blockName}</td>
        <td data-value="${explosionOccurred}">${explosionOccurred ? "بله" : "خیر"}</td>
        <td data-description="${description}">${description}</td>
        <td>
            <button type="button" onclick="removeBlastingDetail(this)" class="btn btn-danger btn-sm">حذف</button>
        </td>`;
        tableBody.appendChild(row);

        console.log("جزئیات آتشباری اضافه شد:", { blockId, blockName, explosionOccurred, description });
        document.getElementById("blasting_block").value = "";
        document.getElementById("blasting_description").value = "";
    };


    window.removeBlastingDetail = function (button) {
        button.closest("tr").remove();
        console.log("یک جزئیات آتشباری حذف شد.");
    };

// مرحله 2: جزئیات حفاری
    window.addDrillingDetail = function () {
        const blockSelect = document.querySelector('[name="drilling_block"]');
        const blockId = blockSelect.value;
         if (!blockId || isNaN(blockId)) {
            alert("لطفاً یک بلوک معتبر انتخاب کنید.");
            return;
        }
        const blockName = blockSelect.options[blockSelect.selectedIndex].text;
        const machineSelect = document.querySelector('[name="drilling_machine"]');
        const machineId = machineSelect.value;
        if (!machineId || isNaN(machineId)) {
            alert("لطفاً یک دستگاه معتبر انتخاب کنید.");
            return;
        }
        const machineName = machineSelect.options[machineSelect.selectedIndex].text;
        const status = document.querySelector('[name="drilling_status"]').value;
        const description = document.querySelector('[name="drilling_description"]').value;


        if (!blockId || isNaN(blockId) || !machineId || isNaN(machineId) || !status) {
            alert("لطفاً تمام فیلدهای موردنیاز را پر کنید.");
            return;
        }

        const tableBody = document.querySelector('#drilling_table tbody');
        const row = document.createElement("tr");

        row.innerHTML = `
        <td data-value="${blockId}">${blockName}</td>
        <td data-value="${machineId}">${machineName}</td>
        <td data-value="${status}">${status}</td>
         <td data-description="${description}">${description}</td>
        <td>
            <button type="button" onclick="removeDrillingDetail(this)" class="btn btn-danger btn-sm">حذف</button>
        </td>`;
        tableBody.appendChild(row);

        console.log("جزئیات حفاری اضافه شد:", { blockId, machineId, status,description });
        document.querySelector('[name="drilling_block"]').value = "";
        document.querySelector('[name="drilling_machine"]').value ="";
        document.querySelector('[name="drilling_status"]').value ="";
        document.querySelector('[name="drilling_description"]').value ="";
    };


    window.removeDrillingDetail = function (button) {
        button.closest("tr").remove();
        console.log("یک جزئیات حفاری حذف شد.");
    };

// مرحله 3: جزئیات بارگیری
    window.addLoadingDetail = function () {
      const blockSelect = document.querySelector('[name="loading_block"]');
        const blockId = blockSelect.value;
         if (!blockId || isNaN(blockId)) {
            alert("لطفاً یک بلوک معتبر انتخاب کنید.");
            return;
        }
        const blockName = blockSelect.options[blockSelect.selectedIndex].text;
        const machineSelect = document.querySelector('[name="loading_machine"]');
        const machineId = machineSelect.value;
        if (!machineId || isNaN(machineId)) {
            alert("لطفاً یک دستگاه معتبر انتخاب کنید.");
            return;
        }
        const machineName = machineSelect.options[machineSelect.selectedIndex].text;
        const status = document.querySelector('[name="loading_status"]').value;
        const description = document.querySelector('[name="loading_description"]').value;

        if (!blockId || !machineId || !status) {
            alert("لطفاً تمام فیلدهای موردنیاز را پر کنید.");
            return;
        }


        const tableBody = document.querySelector('#loading_table tbody');
        const row = document.createElement("tr");

        row.innerHTML = `
         <td data-value="${blockId}">${blockName}</td>
        <td data-value="${machineId}">${machineName}</td>
        <td data-value="${status}">${status}</td>
        <td data-description="${description}">${description}</td>
        <td>
            <button type="button" onclick="removeLoadingDetail(this)" class="btn btn-danger btn-sm">حذف</button>
        </td>`;
        tableBody.appendChild(row);

        console.log("جزئیات بارگیری اضافه شد:", { blockId, machineId, status , description});
       document.querySelector('[name="loading_block"]').value = "";
       document.querySelector('[name="loading_machine"]').value = "";
       document.querySelector('[name="loading_status"]').value = "";
        document.querySelector('[name="loading_description"]').value ="";
    };

    window.removeLoadingDetail = function (button) {
        button.closest("tr").remove();
        console.log("یک جزئیات بارگیری حذف شد.");
    };

// مرحله 4: جزئیات تخلیه
    window.addDumpDetail = function () {
        const dumpSelect = document.querySelector('[name="dump"]');
        const dumpId = dumpSelect.value;
        const dumpName = dumpSelect.options[dumpSelect.selectedIndex].text;
        const status = document.querySelector('[name="dump_status"]').value;
        const description = document.querySelector('[name="dump_description"]').value;

        if (!dumpId || isNaN(dumpId)) {
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
        </td>`;
        tableBody.appendChild(row);

        console.log("جزئیات تخلیه اضافه شد:", { dumpId, dumpName, status, description });
          document.querySelector('[name="dump"]').value = "";
        document.querySelector('[name="dump_status"]').value ="";
        document.querySelector('[name="dump_description"]').value ="";

    };


    window.removeDumpDetail = function (button) {
        button.closest("tr").remove();
        console.log("یک جزئیات تخلیه حذف شد.");
    };
// مرحله 5: نمایش جزئیات بازرسی
    document.getElementById("inspection_done").addEventListener("change", function () {
        const details = document.getElementById("inspection_details");
        details.style.display = this.value === "yes" ? "block" : "none";
        console.log(`وضعیت بازرسی تغییر کرد: ${this.value}`);
    });

    window.addInspectionDetail = function () {
        const inspection_done = document.getElementById("inspection_done").value === "yes";
        const inspection = document.querySelector('[name="inspection"]').value;
        const status = document.querySelector('[name="inspection_safe"]').value;
        const description = document.querySelector('[name="inspection_description"]').value;

        if (!inspection || !status) {
            alert("لطفاً تمام فیلدها را پر کنید.");
            return;
        }

        const tableBody = document.querySelector('#inspection_table tbody');
        const row = document.createElement("tr");

        row.innerHTML = `
          <td data-value="${inspection_done}">${inspection_done ? "بله" : "خیر"}</td>
        <td>${inspection}</td>
        <td>${status}</td>
        <td>${description}</td>
        <td>
            <button type="button" onclick="removeInspectionDetail(this)" class="btn btn-danger btn-sm">حذف</button>
        </td>`;
        tableBody.appendChild(row);

        console.log("جزئیات بازرسی اضافه شد:", { inspection, status, description });
    document.querySelector('[name="inspection"]').value ="";
      document.querySelector('[name="inspection_safe"]').value ="";
         document.querySelector('[name="inspection_description"]').value = "";
    };

    window.removeInspectionDetail = function (button) {
        button.closest("tr").remove();
        console.log("یک جزئیات بازرسی حذف شد.");
    };

// مرحله 6: توقفات
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
        </td>`;
        tableBody.appendChild(row);

        console.log("جزئیات توقفات اضافه شد:", { reason, start, end });
           document.querySelector('[name="stoppage_reason"]').value ="";
        document.querySelector('[name="stoppage_start"]').value ="";
         document.querySelector('[name="stoppage_end"]').value ="";

    };

    window.removeStoppageDetail = function (button) {
        button.closest("tr").remove();
        console.log("یک جزئیات توقف حذف شد.");
    };

// مرحله 7: پیگیری
    let followupDetails = [];

    window.addFollowupDetail = function () {
        const description = document.querySelector('[name="followup_description"]').value;
        const files = document.querySelector('[name="followup_files"]').files;

        if (!description) {
            alert("لطفاً توضیحات را وارد کنید.");
            return;
        }

        const fileArray = [];
        for (let i = 0; i < files.length; i++) {
            fileArray.push(files[i]); // ذخیره فایل‌ها در آرایه
        }

        followupDetails.push({ description, files: fileArray });

        const tableBody = document.querySelector('#followup_table tbody');
        const row = document.createElement("tr");

        let fileNames = fileArray.map(file => file.name).join(", ");

        row.innerHTML = `
        <td>${description}</td>
        <td>${fileNames || "بدون فایل"}</td>
        <td>
            <button type="button" onclick="removeFollowupDetail(this, ${followupDetails.length - 1})" class="btn btn-danger btn-sm">حذف</button>
        </td>`;
        tableBody.appendChild(row);

        console.log("جزئیات پیگیری اضافه شد:", { description, fileNames });
        // پاک کردن فیلدهای ورودی
        document.querySelector('[name="followup_description"]').value = "";
        document.querySelector('[name="followup_files"]').value = "";
    };

    window.removeFollowupDetail = function (button, index) {
        followupDetails.splice(index, 1); // حذف جزئیات از آرایه
        button.closest("tr").remove(); // حذف سطر از جدول
    };

    /** ارسال فرم */
 document.querySelector('[data-kt-stepper-action="submit"]').addEventListener("click", function (e) {
        e.preventDefault();

        const form = document.querySelector("#kt_create_account_form");
        const formData = new FormData(form);

        // جمع‌آوری جزئیات جداول
         const blastingDetails = collectDetailsFromTable('#blasting_table', ['block_id', 'explosion_occurred', 'description']);
        const drillingDetails = collectDetailsFromTable('#drilling_table', ['block_id', 'machine_id', 'status', 'description']);
        const loadingDetails = collectDetailsFromTable('#loading_table', ['block_id', 'machine_id', 'status', 'description']);
        const dumpDetails = collectDetailsFromTable('#dump_table', ['dump_id', 'status', 'description']);
        const stoppageDetails = collectDetailsFromTable('#stoppage_table', ['reason', 'start_time', 'end_time']);
       const inspectionDetails = collectDetailsFromTable('#inspection_table', ['inspection_done','inspection','status', 'description']);

        // تبدیل مقادیر بولی به true/false
         const blastingDetailsConverted = blastingDetails.map(item => ({
            ...item,
            explosion_occurred: item.explosion_occurred === true || item.explosion_occurred === 'true',
        }));


          const inspectionDetailsConverted = inspectionDetails.map(item => ({
            ...item,
            inspection_done: item.inspection_done === true || item.inspection_done === 'true',

        }));



        // ایجاد یک شیء برای داده‌ها
        const data = {
            blasting_details: blastingDetailsConverted,
            drilling_details: drillingDetails,
            loading_details: loadingDetails,
            dump_details: dumpDetails,
            stoppage_details: stoppageDetails,
            inspection_details: inspectionDetailsConverted,
            followups:[]
        };


        // افزودن جزئیات پیگیری
          let followupCounter = 0;
        followupDetails.forEach((detail, index) => {


            data.followups.push({
                followup_description: detail.description,
                //فایلها دیگر در آبجکت data  قرار ندارند
            });
             formData.append(`followup_description_${followupCounter}`, detail.description);
             detail.files.forEach((file, fileIndex) => {
                 formData.append(`followup_file_${followupCounter}_${fileIndex}`, file);
             });
                followupCounter++;
        });

      formData.append("data",JSON.stringify(data))


        // لاگ گرفتن از داده‌های ارسال‌شده
        console.log("داده‌های ارسالی:", [...formData.entries()]);

        // ارسال داده‌ها به سمت سرور
        fetch(form.action, {
            method: "POST",
             body: formData,
            headers: {
                 "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
            },
        })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(errorData => {
                         throw new Error(JSON.stringify(errorData));
                    });
                   // throw new Error(`خطا در پاسخ سرور: ${response.status}`);

                }
                return response.json();
            })
            .then(data => {
                Swal.fire({
                    title: 'گزارش با موفقیت ثبت شد!',
                    text: 'شما به صفحه جزئیات گزارشات هدایت می‌شوید.',
                    icon: 'success',
                    confirmButtonText: 'باشه'
                }).then(() => {
                    window.location.href = `/dailyreport_hse/detail/${data.id}/`;
                });
            })
           .catch(error => {

               try {
                   const errorData = JSON.parse(error.message);
                   let errorMessage = 'مشکلی در ثبت گزارش رخ داد:';

                     if (errorData.errors) {
                      errorMessage = 'مشکلات زیر در ثبت گزارش وجود دارد:<ul>';
                        for (const field in errorData.errors) {
                          errorMessage += `<li>${field}: ${errorData.errors[field].join(", ")}</li>`;
                        }
                        errorMessage += '</ul>';
                     } else if (errorData.error){
                          errorMessage = `مشکلی در ثبت گزارش رخ داد: ${errorData.error}`
                     } else {
                         errorMessage = 'مشکلی در ثبت گزارش رخ داد. لطفا دوباره تلاش کنید'
                     }

                    Swal.fire({
                        title: 'خطا!',
                        html: errorMessage,
                        icon: 'error',
                        confirmButtonText: 'باشه'
                    });
                } catch(e){
                  Swal.fire({
                      title: 'خطا!',
                      text: 'مشکلی در ثبت گزارش رخ داد. لطفاً دوباره تلاش کنید.',
                      icon: 'error',
                      confirmButtonText: 'باشه'
                  });
                 console.error("خطا در ارسال داده‌ها:", error);
               }
           });
    });
});