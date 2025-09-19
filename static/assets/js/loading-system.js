/**
 * سیستم جامع مدیریت Loading States
 * Loading System for HSC Project
 */

class LoadingManager {
    constructor() {
        this.activeLoaders = new Set();
        this.init();
    }

    init() {
        // ایجاد overlay کلی
        this.createGlobalOverlay();
        
        // ایجاد toast container
        this.createToastContainer();
        
        // رویدادهای AJAX
        this.setupAjaxEvents();
        
        // رویدادهای فرم
        this.setupFormEvents();
    }

    createGlobalOverlay() {
        if (document.getElementById('global-loading-overlay')) return;
        
        const overlay = document.createElement('div');
        overlay.id = 'global-loading-overlay';
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">در حال بارگذاری...</span>
                </div>
                <div class="loading-text mt-3">در حال پردازش...</div>
            </div>
        `;
        document.body.appendChild(overlay);
    }

    createToastContainer() {
        if (document.getElementById('toast-container')) return;
        
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }

    // نمایش loading کلی
    showGlobalLoading(text = 'در حال بارگذاری...') {
        const overlay = document.getElementById('global-loading-overlay');
        const textElement = overlay.querySelector('.loading-text');
        textElement.textContent = text;
        overlay.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    // پنهان کردن loading کلی
    hideGlobalLoading() {
        const overlay = document.getElementById('global-loading-overlay');
        overlay.style.display = 'none';
        document.body.style.overflow = '';
    }

    // نمایش skeleton loading
    showSkeleton(container, count = 5) {
        const skeletonHTML = this.generateSkeletonHTML(count);
        container.innerHTML = skeletonHTML;
    }

    generateSkeletonHTML(count) {
        let html = '';
        for (let i = 0; i < count; i++) {
            html += `
                <div class="skeleton-item mb-3 animate-pulse">
                    <div class="d-flex align-items-center">
                        <div class="skeleton-avatar me-3"></div>
                        <div class="flex-grow-1">
                            <div class="skeleton-line mb-2"></div>
                            <div class="skeleton-line-short"></div>
                        </div>
                    </div>
                </div>
            `;
        }
        return html;
    }

    // نمایش progress bar
    showProgress(container, percentage = 0) {
        const progressHTML = `
            <div class="progress mb-3" style="height: 8px;">
                <div class="progress-bar bg-primary progress-bar-striped progress-bar-animated" 
                     role="progressbar" style="width: ${percentage}%">
                </div>
            </div>
        `;
        container.innerHTML = progressHTML;
    }

    // بروزرسانی progress
    updateProgress(container, percentage) {
        const progressBar = container.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = `${percentage}%`;
        }
    }

    // Loading برای دکمه‌ها
    setButtonLoading(button, loading = true) {
        if (loading) {
            button.disabled = true;
            const originalText = button.textContent;
            button.dataset.originalText = originalText;
            button.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                در حال پردازش...
            `;
        } else {
            button.disabled = false;
            button.textContent = button.dataset.originalText || 'ذخیره';
        }
    }

    // Loading برای کارت‌ها
    setCardLoading(card, loading = true) {
        if (loading) {
            const overlay = document.createElement('div');
            overlay.className = 'card-loading-overlay';
            overlay.innerHTML = `
                <div class="text-center">
                    <div class="spinner-border text-primary mb-2" role="status"></div>
                    <div class="small text-muted">در حال بارگذاری...</div>
                </div>
            `;
            card.style.position = 'relative';
            card.appendChild(overlay);
        } else {
            const overlay = card.querySelector('.card-loading-overlay');
            if (overlay) {
                overlay.remove();
            }
        }
    }

    // نمایش toast notification
    showToast(message, type = 'info', duration = 5000) {
        const toastId = 'toast-' + Date.now();
        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = `toast align-items-center text-bg-${type} border-0`;
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${this.getToastIcon(type)} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                        data-bs-dismiss="toast"></button>
            </div>
        `;

        document.getElementById('toast-container').appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast, { delay: duration });
        bsToast.show();

        // حذف خودکار بعد از مخفی شدن
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    getToastIcon(type) {
        const icons = {
            'success': 'check-circle',
            'danger': 'exclamation-triangle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    // تنظیم رویدادهای AJAX
    setupAjaxEvents() {
        // jQuery AJAX events
        if (typeof $ !== 'undefined') {
            $(document).ajaxStart(() => {
                this.showGlobalLoading();
            });

            $(document).ajaxStop(() => {
                this.hideGlobalLoading();
            });

            $(document).ajaxError((event, xhr, settings) => {
                this.showToast('خطا در بارگذاری اطلاعات', 'danger');
            });
        }

        // Fetch API interceptor
        this.interceptFetch();
    }

    interceptFetch() {
        const originalFetch = window.fetch;
        const self = this;

        window.fetch = function(...args) {
            self.showGlobalLoading();
            
            return originalFetch.apply(this, args)
                .then(response => {
                    self.hideGlobalLoading();
                    return response;
                })
                .catch(error => {
                    self.hideGlobalLoading();
                    self.showToast('خطا در ارتباط با سرور', 'danger');
                    throw error;
                });
        };
    }

    // تنظیم رویدادهای فرم
    setupFormEvents() {
        document.addEventListener('submit', (e) => {
            if (e.target.tagName === 'FORM') {
                const submitButton = e.target.querySelector('[type="submit"]');
                if (submitButton) {
                    this.setButtonLoading(submitButton, true);
                    
                    // بازگرداندن حالت بعد از 10 ثانیه (fallback)
                    setTimeout(() => {
                        this.setButtonLoading(submitButton, false);
                    }, 10000);
                }
            }
        });
    }

    // lazy loading تصاویر
    initLazyLoading() {
        const images = document.querySelectorAll('img[data-src]');
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });

        images.forEach(img => imageObserver.observe(img));
    }

    // انیمیشن ورود المان‌ها
    initScrollAnimations() {
        const animatedElements = document.querySelectorAll('.animate-on-scroll');
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animated', 'fadeInUp');
                }
            });
        });

        animatedElements.forEach(el => observer.observe(el));
    }
}

// راه‌اندازی کلاس
const loadingManager = new LoadingManager();

// توابع کمکی عمومی
window.showLoading = (text) => loadingManager.showGlobalLoading(text);
window.hideLoading = () => loadingManager.hideGlobalLoading();
window.showToast = (message, type, duration) => loadingManager.showToast(message, type, duration);
window.setButtonLoading = (button, loading) => loadingManager.setButtonLoading(button, loading);
window.setCardLoading = (card, loading) => loadingManager.setCardLoading(card, loading);

// راه‌اندازی lazy loading و انیمیشن‌ها وقتی DOM آماده شد
document.addEventListener('DOMContentLoaded', () => {
    loadingManager.initLazyLoading();
    loadingManager.initScrollAnimations();
});