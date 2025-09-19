/**
 * Loading Manager
 * HSC Project Enhancement
 */

class LoadingManager {
    constructor() {
        this.init();
        this.activeRequests = 0;
        this.globalLoadingShown = false;
    }

    init() {
        this.createGlobalLoadingOverlay();
        this.setupAjaxInterceptors();
        this.setupFormInterceptors();
    }

    // Create global loading overlay
    createGlobalLoadingOverlay() {
        if (document.querySelector('.global-loading-overlay')) return;

        const overlay = document.createElement('div');
        overlay.className = 'global-loading-overlay';
        overlay.innerHTML = `
            <div class="loading-content">
                <div class="spinner"></div>
                <div class="loading-text">در حال بارگذاری...</div>
            </div>
        `;
        document.body.appendChild(overlay);
    }

    // Show global loading
    showGlobalLoading(message = 'در حال بارگذاری...') {
        const overlay = document.querySelector('.global-loading-overlay');
        if (!overlay) return;

        const textEl = overlay.querySelector('.loading-text');
        if (textEl) textEl.textContent = message;

        overlay.classList.add('active');
        this.globalLoadingShown = true;
        document.body.style.overflow = 'hidden';
    }

    // Hide global loading
    hideGlobalLoading() {
        const overlay = document.querySelector('.global-loading-overlay');
        if (!overlay) return;

        overlay.classList.remove('active');
        this.globalLoadingShown = false;
        document.body.style.overflow = '';
    }

    // Show loading for specific element
    showElementLoading(element, type = 'spinner') {
        if (!element) return;

        element.classList.add('loading-active');

        switch (type) {
            case 'skeleton':
                this.showSkeletonLoading(element);
                break;
            case 'shimmer':
                this.showShimmerLoading(element);
                break;
            case 'button':
                this.showButtonLoading(element);
                break;
            case 'form':
                this.showFormLoading(element);
                break;
            case 'table':
                this.showTableLoading(element);
                break;
            case 'card':
                this.showCardLoading(element);
                break;
            case 'input':
                this.showInputLoading(element);
                break;
            default:
                this.showSpinnerLoading(element);
        }
    }

    // Hide loading for specific element
    hideElementLoading(element) {
        if (!element) return;

        element.classList.remove(
            'loading-active',
            'btn-loading',
            'form-loading',
            'table-loading',
            'card-loading',
            'input-loading'
        );

        // Remove loading elements
        const loadingElements = element.querySelectorAll('.loading-spinner, .skeleton, .loading-overlay');
        loadingElements.forEach(el => el.remove());

        // Restore original content if needed
        if (element.dataset.originalContent) {
            element.innerHTML = element.dataset.originalContent;
            delete element.dataset.originalContent;
        }
    }

    // Skeleton loading
    showSkeletonLoading(element) {
        if (!element.dataset.originalContent) {
            element.dataset.originalContent = element.innerHTML;
        }

        const skeleton = this.createSkeleton(element);
        element.innerHTML = skeleton;
    }

    // Create skeleton based on element type
    createSkeleton(element) {
        if (element.tagName === 'IMG') {
            return '<div class="skeleton skeleton-card"></div>';
        }

        if (element.classList.contains('card')) {
            return `
                <div class="skeleton skeleton-card mb-3"></div>
                <div class="skeleton skeleton-text"></div>
                <div class="skeleton skeleton-text"></div>
                <div class="skeleton skeleton-text" style="width: 60%;"></div>
            `;
        }

        if (element.tagName === 'TABLE' || element.classList.contains('table')) {
            let rows = '';
            for (let i = 0; i < 5; i++) {
                rows += `
                    <tr>
                        <td><div class="skeleton skeleton-text"></div></td>
                        <td><div class="skeleton skeleton-text"></div></td>
                        <td><div class="skeleton skeleton-text"></div></td>
                        <td><div class="skeleton skeleton-text" style="width: 60%;"></div></td>
                    </tr>
                `;
            }
            return `<tbody>${rows}</tbody>`;
        }

        // Default skeleton
        return `
            <div class="skeleton skeleton-text"></div>
            <div class="skeleton skeleton-text"></div>
            <div class="skeleton skeleton-text" style="width: 60%;"></div>
        `;
    }

    // Shimmer loading
    showShimmerLoading(element) {
        element.classList.add('card-loading');
    }

    // Button loading
    showButtonLoading(element) {
        element.classList.add('btn-loading');
        element.disabled = true;
    }

    // Form loading
    showFormLoading(element) {
        element.classList.add('form-loading');
        const inputs = element.querySelectorAll('input, select, textarea, button');
        inputs.forEach(input => input.disabled = true);
    }

    // Table loading
    showTableLoading(element) {
        element.classList.add('table-loading');
    }

    // Card loading
    showCardLoading(element) {
        element.classList.add('card-loading');
    }

    // Input loading
    showInputLoading(element) {
        const wrapper = element.closest('.form-group') || element.parentElement;
        wrapper.classList.add('input-loading');
        element.disabled = true;
    }

    // Spinner loading
    showSpinnerLoading(element) {
        if (element.querySelector('.loading-spinner')) return;

        const spinner = document.createElement('div');
        spinner.className = 'loading-spinner position-absolute top-50 start-50 translate-middle';
        spinner.innerHTML = '<div class="spinner spinner-sm"></div>';

        element.style.position = 'relative';
        element.appendChild(spinner);
        element.style.opacity = '0.7';
    }

    // Progress bar
    showProgress(element, progress = 0, message = '') {
        let progressContainer = element.querySelector('.progress-container');
        
        if (!progressContainer) {
            progressContainer = document.createElement('div');
            progressContainer.className = 'progress-container';
            progressContainer.innerHTML = `
                <div class="progress-bar animated" style="width: 0%"></div>
                <div class="loading-text">${message}</div>
            `;
            element.appendChild(progressContainer);
        }

        const progressBar = progressContainer.querySelector('.progress-bar');
        const loadingText = progressContainer.querySelector('.loading-text');

        if (progressBar) progressBar.style.width = `${Math.min(100, Math.max(0, progress))}%`;
        if (loadingText && message) loadingText.textContent = message;
    }

    // Setup AJAX interceptors
    setupAjaxInterceptors() {
        // jQuery AJAX if available
        if (window.jQuery) {
            const self = this;
            
            jQuery(document).ajaxStart(() => {
                self.activeRequests++;
                if (self.activeRequests === 1 && !self.globalLoadingShown) {
                    setTimeout(() => {
                        if (self.activeRequests > 0) {
                            self.showGlobalLoading();
                        }
                    }, 300); // Delay to avoid flicker for fast requests
                }
            });

            jQuery(document).ajaxStop(() => {
                self.activeRequests = 0;
                self.hideGlobalLoading();
            });

            jQuery(document).ajaxError(() => {
                self.activeRequests = Math.max(0, self.activeRequests - 1);
                if (self.activeRequests === 0) {
                    self.hideGlobalLoading();
                }
            });
        }

        // Fetch API interceptor
        this.setupFetchInterceptor();
    }

    // Setup Fetch interceptor
    setupFetchInterceptor() {
        const originalFetch = window.fetch;
        const self = this;

        window.fetch = function(...args) {
            self.activeRequests++;
            
            if (self.activeRequests === 1 && !self.globalLoadingShown) {
                setTimeout(() => {
                    if (self.activeRequests > 0) {
                        self.showGlobalLoading();
                    }
                }, 300);
            }

            return originalFetch.apply(this, args)
                .finally(() => {
                    self.activeRequests = Math.max(0, self.activeRequests - 1);
                    if (self.activeRequests === 0) {
                        self.hideGlobalLoading();
                    }
                });
        };
    }

    // Setup form interceptors
    setupFormInterceptors() {
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.tagName === 'FORM' && !form.hasAttribute('data-no-loading')) {
                this.showElementLoading(form, 'form');
                
                // Auto-hide loading after reasonable time
                setTimeout(() => {
                    this.hideElementLoading(form);
                }, 30000); // 30 seconds max
            }
        });
    }

    // Lazy load images
    lazyLoadImages() {
        const images = document.querySelectorAll('img[data-src]');
        
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.classList.add('img-lazy');
                        
                        const loadImg = new Image();
                        loadImg.onload = () => {
                            img.src = img.dataset.src;
                            img.classList.add('loaded');
                            img.removeAttribute('data-src');
                        };
                        loadImg.onerror = () => {
                            img.classList.add('loaded'); // Show placeholder
                        };
                        loadImg.src = img.dataset.src;
                        
                        observer.unobserve(img);
                    }
                });
            });

            images.forEach(img => imageObserver.observe(img));
        } else {
            // Fallback for older browsers
            images.forEach(img => {
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
            });
        }
    }

    // Show toast notification
    showToast(message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0 show`;
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        // Add to toast container or create one
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }

        container.appendChild(toast);

        // Auto remove
        setTimeout(() => {
            toast.remove();
        }, duration);

        return toast;
    }

    // Utility methods
    isLoading(element = null) {
        if (element) {
            return element.classList.contains('loading-active');
        }
        return this.globalLoadingShown || this.activeRequests > 0;
    }

    setLoadingText(text) {
        const overlay = document.querySelector('.global-loading-overlay');
        if (overlay) {
            const textEl = overlay.querySelector('.loading-text');
            if (textEl) textEl.textContent = text;
        }
    }

    // Batch operations
    showMultipleLoading(elements, type = 'spinner') {
        elements.forEach(element => {
            this.showElementLoading(element, type);
        });
    }

    hideMultipleLoading(elements) {
        elements.forEach(element => {
            this.hideElementLoading(element);
        });
    }

    // Handle page load
    handlePageLoad() {
        // Auto lazy load images
        this.lazyLoadImages();
        
        // Handle loading buttons
        document.addEventListener('click', (e) => {
            const button = e.target.closest('[data-loading]');
            if (button && !button.disabled) {
                this.showElementLoading(button, 'button');
                
                // Auto-hide after timeout
                setTimeout(() => {
                    this.hideElementLoading(button);
                    button.disabled = false;
                }, 5000);
            }
        });
    }
}

// Initialize loading manager
const loadingManager = new LoadingManager();

// Handle page load
document.addEventListener('DOMContentLoaded', () => {
    loadingManager.handlePageLoad();
});

// Export for global use
window.LoadingManager = LoadingManager;
window.loadingManager = loadingManager;

// Utility functions for easy access
window.showLoading = (element, type) => loadingManager.showElementLoading(element, type);
window.hideLoading = (element) => loadingManager.hideElementLoading(element);
window.showGlobalLoading = (message) => loadingManager.showGlobalLoading(message);
window.hideGlobalLoading = () => loadingManager.hideGlobalLoading();
window.showToast = (message, type, duration) => loadingManager.showToast(message, type, duration);