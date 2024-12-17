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
        const block = document.querySelector('[name="blasting_block"]').value;
        const description = document.querySelector('[name="blasting_description"]').value;

        if (!block) {
            alert("لطفاً بلوک را انتخاب کنید.");
            return;
        }

        const list = document.getElementById("blasting_items");
        const item = document.createElement("li");
        item.textContent = `بلوک: ${block} - توضیحات: ${description}`;
        list.appendChild(item);
    };

    /** جزئیات حفاری */
    window.addDrillingDetail = function () {
        const block = document.querySelector('[name="drilling_block"]').value;
        const machine = document.querySelector('[name="drilling_machine"]').value;
        const status = document.querySelector('[name="drilling_status"]').value;

        if (!block || !machine || !status) {
            alert("لطفاً تمام فیلدها را پر کنید.");
            return;
        }

        const list = document.getElementById("drilling_items");
        const item = document.createElement("li");
        item.textContent = `بلوک: ${block} | دستگاه: ${machine} | وضعیت: ${status}`;
        list.appendChild(item);
    };

       /** جزئیات بارگیری */
    window.addLoadingDetail = function () {
        const block = document.querySelector('[name="loading_block"]').value;
        const machine = document.querySelector('[name="loading_machine"]').value;
        const status = document.querySelector('[name="loading_status"]').value;

        if (!block || !machine || !status) {
            alert("لطفاً تمام فیلدها را پر کنید.");
            return;
        }

        const list = document.getElementById("loading_items");
        const item = document.createElement("li");
        item.textContent = `بلوک: ${block} | دستگاه: ${machine} | وضعیت: ${status}`;
        list.appendChild(item);
    };


    /** جزئیات تخلیه */
    window.addDumpDetail = function () {
        const dump = document.querySelector('[name="dump"]').value;
        const status = document.querySelector('[name="dump_status"]').value;
        const description = document.querySelector('[name="dump_description"]').value;

        if (!dump || !status) {
            alert("لطفاً تمام فیلدها را پر کنید.");
            return;
        }

        const list = document.getElementById("dump_items");
        const item = document.createElement("li");
        item.textContent = `دامپ: ${dump} | وضعیت: ${status} | توضیحات: ${description}`;
        list.appendChild(item);
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

        const list = document.getElementById("inspection_items");
        const item = document.createElement("li");
        item.textContent = `بازرسی: ${inspection} | وضعیت: ${status} | توضیحات: ${description}`;
        list.appendChild(item);
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

        const list = document.getElementById("stoppage_items");
        const item = document.createElement("li");
        item.textContent = `علت توقف: ${reason} | زمان: ${start} تا ${end}`;
        list.appendChild(item);
    };

    /** پیگیری */
    window.addFollowupDetail = function () {
        const description = document.querySelector('[name="followup_description"]').value;
        const files = document.querySelector('[name="followup_files"]').files;

        if (!description) {
            alert("لطفاً توضیحات را وارد کنید.");
            return;
        }

        const list = document.getElementById("followup_items");
        const item = document.createElement("li");
        item.textContent = `توضیحات: ${description}`;
        list.appendChild(item);

        // نمایش نام فایل‌ها
        for (let i = 0; i < files.length; i++) {
            const fileItem = document.createElement("li");
            fileItem.textContent = `فایل: ${files[i].name}`;
            list.appendChild(fileItem);
        }
    };

    /** ارسال فرم */
    document.querySelector('[data-kt-stepper-action="submit"]').addEventListener("click", function (e) {
        e.preventDefault();
        alert("فرم با موفقیت ثبت شد!");
        document.querySelector("#kt_create_account_form").submit();
    });
});
