document.addEventListener('DOMContentLoaded', function () {
    // مدیریت نمایش بلوک آتش‌باری
    const blastingDoneElement = document.getElementById('blasting_done');
    if (blastingDoneElement) {
        blastingDoneElement.addEventListener('change', function () {
            const blockContainer = document.getElementById('blasting_block_container');
            blockContainer.style.display = this.value === 'yes' ? 'block' : 'none';
        });
    }

    // مدیریت استپ‌ها
    const stepperElement = document.querySelector("#kt_create_account_stepper");
    if (stepperElement) {
        const stepper = new KTStepper(stepperElement);

        document.querySelectorAll('[data-kt-stepper-action="next"]').forEach(btn =>
            btn.addEventListener('click', () => {
                if (validateCurrentStep(stepper.getCurrentStepIndex())) {
                    stepper.goNext();
                }
            })
        );

        document.querySelectorAll('[data-kt-stepper-action="previous"]').forEach(btn =>
            btn.addEventListener('click', () => {
                stepper.goPrevious();
            })
        );
    }

    // مدیریت فرم
    const form = document.querySelector('#kt_create_account_form');
    if (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            if (validateAllSteps()) {
                form.submit();
            }
        });
    }

    // اعتبارسنجی مراحل
    function validateCurrentStep(stepIndex) {
        switch (stepIndex) {
            case 1:
                return validateBlasting();
            case 2:
                return validateDrilling();
            case 3:
                return validateLoading();
            case 4:
                return validateInspection();
            case 5:
                return validateSafety();
            default:
                return true;
        }
    }

    function validateAllSteps() {
        for (let i = 1; i <= 5; i++) {
            if (!validateCurrentStep(i)) {
                alert(`مرحله ${i} به درستی تکمیل نشده است.`);
                return false;
            }
        }
        return true;
    }

    function validateBlasting() {
        const blastingDone = document.querySelector('[name="blasting_done"]:checked');
        const block = document.querySelector('[name="blasting_block"]');
        if (!blastingDone) {
            alert("لطفاً وضعیت آتش‌باری را انتخاب کنید.");
            return false;
        }
        if (blastingDone.value === 'yes' && (!block || !block.value)) {
            alert("لطفاً بلوک آتش‌باری را انتخاب کنید.");
            return false;
        }
        return true;
    }

    function validateDrilling() {
        const drillingSite = document.querySelector('[name="drilling_site"]');
        const drillingMachine = document.querySelector('[name="drilling_machine"]');
        if (!drillingSite || !drillingSite.value) {
            alert("لطفاً سایت حفاری را انتخاب کنید.");
            return false;
        }
        if (!drillingMachine || !drillingMachine.value) {
            alert("لطفاً دستگاه حفاری را انتخاب کنید.");
            return false;
        }
        return true;
    }

    function validateLoading() {
        const workface = document.querySelector('[name="loading_workface"]');
        const dump = document.querySelector('[name="loading_dump"]');
        if (!workface || !workface.value) {
            alert("لطفاً جبهه کاری را انتخاب کنید.");
            return false;
        }
        if (!dump || !dump.value) {
            alert("لطفاً دمپ را انتخاب کنید.");
            return false;
        }
        return true;
    }

    function validateInspection() {
        const inspectionDone = document.querySelector('[name="inspection_done"]:checked');
        if (!inspectionDone) {
            alert("لطفاً وضعیت بازدید تعمیرگاه را مشخص کنید.");
            return false;
        }
        return true;
    }

    function validateSafety() {
        const safetyIssues = document.querySelectorAll('[name="safety_issues[]"]');
        if (safetyIssues.length === 0) {
            alert("لطفاً حداقل یک مشکل ایمنی ثبت کنید.");
            return false;
        }
        return true;
    }
});
