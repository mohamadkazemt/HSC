/**
 * اعتبارسنجی فرم ارزیابی ریسک - سمت کلاینت
 * برای بهبود تجربه کاربری و کاهش درخواست‌های سرور
 */

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('risk-form');
    if (!form) return;

    // عناصر فرم
    const riskSource = document.getElementById('id_risk_source');
    const riskSourceOther = document.getElementById('id_risk_source_other');
    const hasLegalRequirement = document.getElementById('id_has_legal_requirement');
    const legalRequirementDesc = document.getElementById('id_legal_requirement_desc');
    const isLegalCompliant = document.getElementById('id_is_legal_compliant');
    const correctiveActionRequired = document.getElementById('id_corrective_action_required');
    const actionDeadline = document.getElementById('id_action_deadline');
    const actionDate = document.getElementById('id_action_date');
    const responsiblePerson = document.getElementById('id_responsible_person');
    const isMue = document.getElementById('id_is_mue');
    const mueCode = document.getElementById('id_mue_code');
    const isEmergency = document.getElementById('id_is_emergency');
    const emergencyCode = document.getElementById('id_emergency_code');
    const probability = document.getElementById('id_probability');
    const severity = document.getElementById('id_severity');

    /**
     * نمایش پیام خطا برای یک فیلد
     */
    function showError(field, message) {
        if (!field) return;
        
        // حذف خطای قبلی
        clearError(field);
        
        // اضافه کردن کلاس خطا
        field.classList.add('border-red-400', 'focus:border-red-500', 'focus:ring-red-500');
        
        // ایجاد المنت خطا
        const errorDiv = document.createElement('div');
        errorDiv.className = 'text-xs text-red-600 dark:text-red-400 mt-1 validation-error';
        errorDiv.innerHTML = `<i class="fa-solid fa-circle-exclamation"></i> ${message}`;
        
        // اضافه کردن به DOM
        field.parentElement.appendChild(errorDiv);
    }

    /**
     * پاک کردن پیام خطا از یک فیلد
     */
    function clearError(field) {
        if (!field) return;
        
        field.classList.remove('border-red-400', 'focus:border-red-500', 'focus:ring-red-500');
        
        const errorDiv = field.parentElement.querySelector('.validation-error');
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    /**
     * پاک کردن همه خطاها
     */
    function clearAllErrors() {
        document.querySelectorAll('.validation-error').forEach(el => el.remove());
        document.querySelectorAll('input, select, textarea').forEach(el => {
            el.classList.remove('border-red-400', 'focus:border-red-500', 'focus:ring-red-500');
        });
    }

    /**
     * اعتبارسنجی فیلد "سایر" منشا ریسک
     */
    function validateRiskSourceOther() {
        if (riskSource && riskSource.value === 'other') {
            if (!riskSourceOther || !riskSourceOther.value.trim()) {
                showError(riskSourceOther, 'لطفاً منشا را توضیح دهید.');
                return false;
            }
        }
        clearError(riskSourceOther);
        return true;
    }

    /**
     * اعتبارسنجی الزامات قانونی
     */
    function validateLegalRequirement() {
        if (hasLegalRequirement && hasLegalRequirement.checked) {
            let isValid = true;
            
            if (!legalRequirementDesc || !legalRequirementDesc.value.trim()) {
                showError(legalRequirementDesc, 'لطفاً الزام قانونی را شرح دهید.');
                isValid = false;
            } else {
                clearError(legalRequirementDesc);
            }
            
            if (!isLegalCompliant || !isLegalCompliant.value) {
                showError(isLegalCompliant, 'لطفاً وضعیت رعایت الزام قانونی را مشخص کنید.');
                isValid = false;
            } else {
                clearError(isLegalCompliant);
            }
            
            return isValid;
        }
        clearError(legalRequirementDesc);
        clearError(isLegalCompliant);
        return true;
    }

    /**
     * اعتبارسنجی اقدامات اصلاحی
     */
    function validateCorrectiveAction() {
        if (correctiveActionRequired && correctiveActionRequired.checked) {
            let isValid = true;
            
            if (!actionDeadline || !actionDeadline.value) {
                showError(actionDeadline, 'لطفاً مهلت اقدام را مشخص کنید.');
                isValid = false;
            } else {
                clearError(actionDeadline);
                
                // بررسی منطقی بودن تاریخ‌ها
                if (actionDate && actionDate.value && actionDeadline.value) {
                    if (new Date(actionDate.value) > new Date(actionDeadline.value)) {
                        showError(actionDeadline, 'مهلت اقدام نمی‌تواند قبل از تاریخ اقدام باشد.');
                        isValid = false;
                    }
                }
            }
            
            if (!responsiblePerson || !responsiblePerson.value) {
                showError(responsiblePerson, 'لطفاً مسئول اجرا را مشخص کنید.');
                isValid = false;
            } else {
                clearError(responsiblePerson);
            }
            
            return isValid;
        }
        clearError(actionDeadline);
        clearError(responsiblePerson);
        return true;
    }

    /**
     * اعتبارسنجی MUE
     */
    function validateMUE() {
        if (isMue && isMue.checked) {
            if (!mueCode || !mueCode.value.trim()) {
                showError(mueCode, 'لطفاً کد MUE را وارد کنید.');
                return false;
            }
        }
        clearError(mueCode);
        return true;
    }

    /**
     * اعتبارسنجی شرایط اضطراری
     */
    function validateEmergency() {
        if (isEmergency && isEmergency.checked) {
            if (!emergencyCode || !emergencyCode.value.trim()) {
                showError(emergencyCode, 'لطفاً کد شرایط اضطراری را وارد کنید.');
                return false;
            }
        }
        clearError(emergencyCode);
        return true;
    }

    /**
     * اعتبارسنجی احتمال و شدت
     */
    function validateProbabilitySeverity() {
        let isValid = true;
        
        if (!probability || !probability.value) {
            showError(probability, 'لطفاً احتمال وقوع را انتخاب کنید.');
            isValid = false;
        } else {
            clearError(probability);
        }
        
        if (!severity || !severity.value) {
            showError(severity, 'لطفاً شدت پیامد را انتخاب کنید.');
            isValid = false;
        } else {
            clearError(severity);
        }
        
        return isValid;
    }

    /**
     * اعتبارسنجی فیلدهای اجباری اصلی
     */
    function validateRequiredFields() {
        let isValid = true;
        
        const activityComponent = document.getElementById('id_activity_component');
        if (activityComponent && !activityComponent.value.trim()) {
            showError(activityComponent, 'این فیلد الزامی است.');
            isValid = false;
        } else if (activityComponent) {
            clearError(activityComponent);
        }
        
        const hazard = document.getElementById('id_hazard');
        if (hazard && !hazard.value) {
            showError(hazard, 'لطفاً نوع خطر را انتخاب کنید.');
            isValid = false;
        } else if (hazard) {
            clearError(hazard);
        }
        
        const potentialEvent = document.getElementById('id_potential_event');
        if (potentialEvent && !potentialEvent.value.trim()) {
            showError(potentialEvent, 'لطفاً رویداد احتمالی را مشخص کنید.');
            isValid = false;
        } else if (potentialEvent) {
            clearError(potentialEvent);
        }
        
        const causes = document.getElementById('id_causes');
        if (causes && !causes.value.trim()) {
            showError(causes, 'لطفاً علل احتمالی وقوع را شرح دهید.');
            isValid = false;
        } else if (causes) {
            clearError(causes);
        }
        
        const consequence = document.getElementById('id_consequence');
        if (consequence && !consequence.value) {
            showError(consequence, 'لطفاً نوع پیامد را انتخاب کنید.');
            isValid = false;
        } else if (consequence) {
            clearError(consequence);
        }
        
        const existingControls = document.getElementById('id_existing_controls');
        if (existingControls && !existingControls.value.trim()) {
            showError(existingControls, 'لطفاً کنترل‌های موجود را شرح دهید.');
            isValid = false;
        } else if (existingControls) {
            clearError(existingControls);
        }
        
        const controlFailureCauses = document.getElementById('id_control_failure_causes');
        if (controlFailureCauses && !controlFailureCauses.value.trim()) {
            showError(controlFailureCauses, 'لطفاً علل احتمالی شکست کنترل‌ها را شرح دهید.');
            isValid = false;
        } else if (controlFailureCauses) {
            clearError(controlFailureCauses);
        }
        
        return isValid;
    }

    /**
     * اعتبارسنجی کامل فرم
     */
    function validateForm() {
        clearAllErrors();
        
        const validations = [
            validateRequiredFields(),
            validateRiskSourceOther(),
            validateLegalRequirement(),
            validateProbabilitySeverity(),
            validateCorrectiveAction(),
            validateMUE(),
            validateEmergency()
        ];
        
        return validations.every(v => v === true);
    }

    // اضافه کردن event listener برای submit
    form.addEventListener('submit', function(e) {
        if (!validateForm()) {
            e.preventDefault();
            
            // اسکرول به اولین خطا
            const firstError = document.querySelector('.validation-error');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            
            // نمایش پیام کلی
            alert('لطفاً خطاهای فرم را برطرف کنید.');
        }
    });

    // اضافه کردن event listener برای تغییرات realtime
    if (riskSource) {
        riskSource.addEventListener('change', validateRiskSourceOther);
    }
    
    if (hasLegalRequirement) {
        hasLegalRequirement.addEventListener('change', validateLegalRequirement);
    }
    
    if (correctiveActionRequired) {
        correctiveActionRequired.addEventListener('change', validateCorrectiveAction);
    }
    
    if (isMue) {
        isMue.addEventListener('change', validateMUE);
    }
    
    if (isEmergency) {
        isEmergency.addEventListener('change', validateEmergency);
    }
    
    if (actionDate && actionDeadline) {
        actionDate.addEventListener('change', validateCorrectiveAction);
        actionDeadline.addEventListener('change', validateCorrectiveAction);
    }
    
    // پاک کردن خطا هنگام تغییر مقدار
    form.querySelectorAll('input, select, textarea').forEach(field => {
        field.addEventListener('input', function() {
            clearError(this);
        });
        field.addEventListener('change', function() {
            clearError(this);
        });
    });
});
