﻿"use strict";

// Class definition
var KTModalUpdateCustomer = function () {
    var element;
    var submitButton;
    var cancelButton;
    var closeButton;
    var form;
    var modal;

    // Init form inputs
    var initForm = function () {
        // Action buttons
        submitButton.addEventListener('click', function (e) {
            // Prevent default button action
            e.preventDefault();

            // Show loading indication
            submitButton.setAttribute('data-kt-indicator', 'on');

            // Simulate form submission
            setTimeout(function () {
                // Simulate form submission
                submitButton.removeAttribute('data-kt-indicator');

                // Show popup confirmation 
                Swal.fire({
                    text: "فرم با موفقیت ثبت شد!",
                    icon: "success",
                    buttonsStyling: false,
                    confirmButtonText: "Ok, got it!",
                    customClass: {
                        confirmButton: "btn btn-primary"
                    }
                }).then(function (result) {
                    if (result.isConfirmed) {
                        modal.hide();
                    }
                });

                //form.submit(); // Submit form
            }, 2000);
        });

        cancelButton.addEventListener('click', function (e) {
            e.preventDefault();

            Swal.fire({
                text: "آیا مطمئن هستید که می خواهید لغو کنید؟?",
                icon: "warning",
                showCancelButton: true,
                buttonsStyling: false,
                confirmButtonText: "بله ، آن را لغو کنید!",
                cancelButtonText: "خیر",
                customClass: {
                    confirmButton: "btn btn-primary",
                    cancelButton: "btn btn-active-light"
                }
            }).then(function (result) {
                if (result.value) {
                    form.reset(); // Reset form	
                    modal.hide(); // Hide modal				
                } else if (result.dismiss === 'cancel') {
                    Swal.fire({
                        text: "فرم شما لغو نشده است !.",
                        icon: "error",
                        buttonsStyling: false,
                        confirmButtonText: "Ok, got it!",
                        customClass: {
                            confirmButton: "btn btn-primary",
                        }
                    });
                }
            });
        });

        closeButton.addEventListener('click', function (e) {
            e.preventDefault();

            Swal.fire({
                text: "آیا مطمئن هستید که می خواهید لغو کنید؟?",
                icon: "warning",
                showCancelButton: true,
                buttonsStyling: false,
                confirmButtonText: "بله ، آن را لغو کنید!",
                cancelButtonText: "خیر",
                customClass: {
                    confirmButton: "btn btn-primary",
                    cancelButton: "btn btn-active-light"
                }
            }).then(function (result) {
                if (result.value) {
                    form.reset(); // Reset form	
                    modal.hide(); // Hide modal				
                } else if (result.dismiss === 'cancel') {
                    Swal.fire({
                        text: "فرم شما لغو نشده است !.",
                        icon: "error",
                        buttonsStyling: false,
                        confirmButtonText: "Ok, got it!",
                        customClass: {
                            confirmButton: "btn btn-primary",
                        }
                    });
                }
            });
        });
    }

    return {
        // Public functions
        init: function () {
            // Elements
            element = document.querySelector('#kt_modal_update_customer');
            modal = new bootstrap.Modal(element);

            form = element.querySelector('#kt_modal_update_customer_form');
            submitButton = form.querySelector('#kt_modal_update_customer_submit');
            cancelButton = form.querySelector('#kt_modal_update_customer_cancel');
            closeButton = element.querySelector('#kt_modal_update_customer_close');

            initForm();
        }
    };
}();

// On document ready
KTUtil.onDOMContentLoaded(function () {
    KTModalUpdateCustomer.init();
});




// سایر کدهای فایل update.js

document.addEventListener('DOMContentLoaded', function() {
    const messagesDiv = document.querySelector('.messages');
    if (messagesDiv) {
        const messages = messagesDiv.querySelectorAll('.alert');
        messages.forEach(message => {
            // نمایش پیغام در Console به عنوان تست، این را می‌توان تغییر داد به نمایش دلخواه
            console.log(message.textContent);

            // اضافه کردن کد برای نمایش بهتر پیغام‌ها با استفاده از alert یا نمایش زیباتر
            alert(message.textContent);
        });
    }
});
