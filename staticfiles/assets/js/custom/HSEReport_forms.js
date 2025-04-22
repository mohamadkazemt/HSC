// JavaScript file to manage the stepper form in dailyreport_hse application
document.addEventListener("DOMContentLoaded", function () {
    const stepperElement = document.getElementById("kt_create_account_stepper");
    const stepperForm = document.getElementById("kt_create_account_form");
    const steps = document.querySelectorAll(".stepper-item");
    const contents = document.querySelectorAll("[data-kt-stepper-element='content']");
    const nextButton = document.querySelector("[data-kt-stepper-action='next']");
    const prevButton = document.querySelector("[data-kt-stepper-action='previous']");
    const submitButton = document.querySelector("[data-kt-stepper-action='submit']");

    let currentStep = parseInt(document.querySelector("input[name='step']")?.value) || 1;

    function showStep(step) {
        steps.forEach((stepElement, index) => {
            const content = contents[index];
            if (content) {  // بررسی اینکه عنصر وجود دارد
                if (index + 1 === step) {
                    stepElement.classList.add("current");
                    stepElement.classList.remove("completed");
                    content.style.display = "block";
                } else {
                    stepElement.classList.remove("current");
                    content.style.display = "none";
                    if (index + 1 < step) {
                        stepElement.classList.add("completed");
                    } else {
                        stepElement.classList.remove("completed");
                    }
                }
            }
        });
    }


    if (prevButton) {
        prevButton.addEventListener("click", function (event) {
            event.preventDefault();
            if (currentStep > 1) {
                currentStep--;
                showStep(currentStep);
            }
        });
    }

    if (nextButton) {
        nextButton.addEventListener("click", function (event) {
            event.preventDefault();
            if (currentStep < steps.length) {
                currentStep++;
                showStep(currentStep);
            }
        });
    }

    if (submitButton) {
        submitButton.addEventListener("click", function (event) {
            event.preventDefault();
            // Automatically submit data for step 1 without form
            if (currentStep === 1) {
                fetch("/dailyreport_hse/auto_create_report/", {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": document.querySelector("input[name='csrfmiddlewaretoken']").value,
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({})
                }).then(response => {
                    if (response.ok) {
                        currentStep++;
                        showStep(currentStep);
                    } else {
                        alert("خطایی رخ داد. لطفاً دوباره تلاش کنید.");
                    }
                });
            } else {
                stepperForm.submit();
            }
        });
    }

    // Initialize the first step
    showStep(currentStep);

    // Dynamic field management (example for additional items in steps)
    function addDynamicItem(section, fields) {
        const list = document.getElementById(`${section}_items`);
        const listItem = document.createElement("li");
        const values = fields.map((field) => document.querySelector(`[name='${section}_${field}']`).value);

        if (values.some((value) => !value)) {
            alert("لطفاً همه فیلدها را پر کنید.");
            return;
        }

        listItem.textContent = values.join(" | ");
        list.appendChild(listItem);

        fields.forEach((field) => {
            const input = document.querySelector(`[name='${section}_${field}']`);
            if (input) input.value = "";
        });
    }

    // Example for dynamic items
    document.getElementById("add_loading_item")?.addEventListener("click", function () {
        addDynamicItem("loading", ["stone_type", "load_count"]);
    });

    document.getElementById("add_machine_status")?.addEventListener("click", function () {
        addDynamicItem("machine", ["block", "status", "reason"]);
    });

    // Additional setups for dynamic sections if required
});
