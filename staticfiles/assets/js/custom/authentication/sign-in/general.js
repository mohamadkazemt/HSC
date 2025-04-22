"use strict";

// Class definition
var KTSigninGeneral = function () {
    // Elements
    var form;
    var submitButton;
    var validator;

    // Handle form
    var handleValidation = function (e) {
        // Init form validation rules. For more info check the FormValidation plugin's official documentation:https://formvalidation.io/
        validator = FormValidation.formValidation(
            form,
            {
                fields: {
                    'username': { // باید با نام فیلدهای فرم جنگو تطابق داشته باشد
                        validators: {
                            notEmpty: {
                                message: 'نام کاربری الزامی است'
                            }
                        }
                    },
                    'password': {
                        validators: {
                            notEmpty: {
                                message: 'رمز عبور الزامی است'
                            }
                        }
                    }
                },
                plugins: {
                    trigger: new FormValidation.plugins.Trigger(),
                    bootstrap: new FormValidation.plugins.Bootstrap5({
                        rowSelector: '.fv-row',
                        eleInvalidClass: '',  // comment to enable invalid state icons
                        eleValidClass: '' // comment to enable valid state icons
                    })
                }
            }
        );
    }

    var handleSubmitAjax = function (e) {
        // Handle form submit
        submitButton.addEventListener('click', function (e) {
            // Prevent button default action
            e.preventDefault();

            // Validate form
            validator.validate().then(function (status) {
                if (status == 'Valid') {
                    // Show loading indication
                    submitButton.setAttribute('data-kt-indicator', 'on');

                    // Disable button to avoid multiple clicks
                    submitButton.disabled = true;

                    // ارسال درخواست به سمت سرور جنگو
                    axios.post(submitButton.closest('form').getAttribute('action'), new FormData(form))
                        .then(function (response) {
                            if (response.data.success) {
                                // Login successful
                                Swal.fire({
                                    text: "شما با موفقیت وارد شدید!",
                                    icon: "success",
                                    buttonsStyling: false,
                                    confirmButtonText: "باشه!",
                                    customClass: {
                                        confirmButton: "btn btn-primary"
                                    }
                                }).then(function () {
                                    const redirectUrl = form.getAttribute('data-kt-redirect-url');
                                    if (redirectUrl) {
                                        location.href = redirectUrl;
                                    }
                                });
                            } else {
                                // Login failed
                                Swal.fire({
                                    text: response.data.message || "نام کاربری یا رمز عبور اشتباه است.",
                                    icon: "error",
                                    buttonsStyling: false,
                                    confirmButtonText: "باشه!",
                                    customClass: {
                                        confirmButton: "btn btn-primary"
                                    }
                                });
                            }
                        })
                        .catch(function (error) {
                            Swal.fire({
                                text: "متاسفانه خطایی رخ داده است. لطفا دوباره تلاش کنید.",
                                icon: "error",
                                buttonsStyling: false,
                                confirmButtonText: "باشه!",
                                customClass: {
                                    confirmButton: "btn btn-primary"
                                }
                            });
                        })
                        .then(() => {
                            // Hide loading indication
                            submitButton.removeAttribute('data-kt-indicator');
                            // Enable button
                            submitButton.disabled = false;
                        });
                } else {
                    Swal.fire({
                        text: "لطفا خطاهای موجود در فرم را برطرف کنید.",
                        icon: "error",
                        buttonsStyling: false,
                        confirmButtonText: "باشه!",
                        customClass: {
                            confirmButton: "btn btn-primary"
                        }
                    });
                }
            });
        });
    }

    // Public functions
    return {
        // Initialization
        init: function () {
            form = document.querySelector('#kt_sign_in_form');
            submitButton = document.querySelector('#kt_sign_in_submit');

            handleValidation();
            handleSubmitAjax();
        }
    };
}();

// On document ready
KTUtil.onDOMContentLoaded(function () {
    KTSigninGeneral.init();
});
