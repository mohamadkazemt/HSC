/**
 * Performance Optimization System
 * HSC Project Enhancement
 */

class PerformanceOptimizer {
    constructor() {
        this.init();
    }

    init() {
        this.optimizeImages();
        this.lazyLoadComponents();
        this.prefetchResources();
        this.optimizeAnimations();
        this.setupServiceWorker();
    }

    // بهینه‌سازی تصاویر
    optimizeImages() {
        // تبدیل img tags به lazy loading
        document.querySelectorAll('img').forEach(img => {
            if (!img.hasAttribute('loading')) {
                img.setAttribute('loading', 'lazy');
            }
            
            // اضافه کردن placeholder
            if (!img.src && !img.dataset.src) {
                img.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 200"%3E%3Crect fill="%23e9ecef" width="300" height="200"/%3E%3C/svg%3E';
            }
        });

        // Intersection Observer برای lazy loading
        if ('IntersectionObserver' in window) {
            this.setupImageLazyLoading();
        }
    }

    setupImageLazyLoading() {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    
                    // اگر data-src دارد، آن را load کن
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                    }
                    
                    // اضافه کردن کلاس loaded برای انیمیشن
                    img.addEventListener('load', () => {
                        img.classList.add('loaded');
                    });
                    
                    observer.unobserve(img);
                }
            });
        }, {
            rootMargin: '50px 0px',
            threshold: 0.01
        });

        document.querySelectorAll('img[data-src], img[loading="lazy"]').forEach(img => {
            imageObserver.observe(img);
        });
    }

    // Lazy loading کامپوننت‌ها
    lazyLoadComponents() {
        // Lazy load charts
        this.lazyLoadCharts();
        
        // Lazy load heavy components
        this.lazyLoadHeavyComponents();
    }

    lazyLoadCharts() {
        const chartContainers = document.querySelectorAll('[data-chart]');
        
        if (chartContainers.length > 0) {
            const chartObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.loadChart(entry.target);
                        chartObserver.unobserve(entry.target);
                    }
                });
            });

            chartContainers.forEach(container => {
                chartObserver.observe(container);
            });
        }
    }

    async loadChart(container) {
        const chartType = container.dataset.chart;
        
        try {
            // نمایش loading
            container.innerHTML = `
                <div class="text-center p-4">
                    <div class="spinner-border text-primary mb-2"></div>
                    <div class="small text-muted">بارگذاری نمودار...</div>
                </div>
            `;

            // Load Chart.js if not loaded
            if (!window.Chart) {
                await this.loadScript('/static/assets/plugins/custom/chart.js/chart.bundle.js');
            }

            // Initialize chart based on type
            this.initializeChart(container, chartType);
            
        } catch (error) {
            console.error('Error loading chart:', error);
            container.innerHTML = '<div class="alert alert-danger">خطا در بارگذاری نمودار</div>';
        }
    }

    initializeChart(container, type) {
        // Implementation based on chart type
        const ctx = document.createElement('canvas');
        container.innerHTML = '';
        container.appendChild(ctx);

        // Sample chart configuration
        new Chart(ctx, {
            type: type,
            data: {
                labels: ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور'],
                datasets: [{
                    label: 'آمار',
                    data: [12, 19, 3, 5, 2, 3],
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'نمودار آماری'
                    }
                }
            }
        });
    }

    lazyLoadHeavyComponents() {
        // DataTables lazy loading
        const tables = document.querySelectorAll('[data-datatable]');
        
        if (tables.length > 0) {
            const tableObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.initializeDataTable(entry.target);
                        tableObserver.unobserve(entry.target);
                    }
                });
            });

            tables.forEach(table => {
                tableObserver.observe(table);
            });
        }
    }

    async initializeDataTable(table) {
        try {
            // Load DataTables if not loaded
            if (!window.DataTable && !$.fn.DataTable) {
                await this.loadScript('/static/assets/plugins/custom/datatables/datatables.bundle.js');
                await this.loadCSS('/static/assets/plugins/custom/datatables/datatables.bundle.css');
            }

            // Initialize DataTable
            $(table).DataTable({
                responsive: true,
                language: {
                    url: '/static/assets/plugins/custom/datatables/fa.json'
                },
                pageLength: 25,
                dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>' +
                     '<"row"<"col-sm-12"tr>>' +
                     '<"row"<"col-sm-12 col-md-5"i><"col-sm-12 col-md-7"p>>',
            });

        } catch (error) {
            console.error('Error initializing DataTable:', error);
        }
    }

    // Prefetch resources
    prefetchResources() {
        // Prefetch critical pages
        this.prefetchCriticalPages();
        
        // Prefetch on hover
        this.setupHoverPrefetch();
    }

    prefetchCriticalPages() {
        const criticalPages = [
            '/dashboard/',
            '/core/logs/',
            '/accounts/profile/'
        ];

        criticalPages.forEach(url => {
            const link = document.createElement('link');
            link.rel = 'prefetch';
            link.href = url;
            document.head.appendChild(link);
        });
    }

    setupHoverPrefetch() {
        const prefetched = new Set();
        
        document.addEventListener('mouseover', (e) => {
            const link = e.target.closest('a[href]');
            if (link && link.href && !prefetched.has(link.href) && this.shouldPrefetch(link.href)) {
                this.prefetchPage(link.href);
                prefetched.add(link.href);
            }
        });
    }

    shouldPrefetch(url) {
        // Only prefetch internal links
        return url.startsWith(window.location.origin) && 
               !url.includes('#') && 
               !url.includes('logout') &&
               !url.includes('download');
    }

    prefetchPage(url) {
        const link = document.createElement('link');
        link.rel = 'prefetch';
        link.href = url;
        document.head.appendChild(link);
    }

    // Animation optimization
    optimizeAnimations() {
        // Reduce animations for users who prefer reduced motion
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            document.documentElement.style.setProperty('--animation-duration', '0.001ms');
            document.documentElement.style.setProperty('--transition-duration', '0.001ms');
        }

        // Use requestAnimationFrame for smooth animations
        this.setupSmoothAnimations();
    }

    setupSmoothAnimations() {
        const animatedElements = document.querySelectorAll('.animate-counter');
        
        animatedElements.forEach(el => {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.animateCounter(entry.target);
                        observer.unobserve(entry.target);
                    }
                });
            });
            
            observer.observe(el);
        });
    }

    animateCounter(element) {
        const targetValue = parseInt(element.textContent.replace(/[^\d]/g, ''));
        const duration = 2000; // 2 seconds
        const startTime = performance.now();
        
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function
            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
            const currentValue = Math.floor(targetValue * easeOutQuart);
            
            element.textContent = currentValue.toLocaleString('fa-IR');
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }

    // Service Worker setup
    setupServiceWorker() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/static/service-worker.js')
                .then(registration => {
                    console.log('Service Worker registered:', registration);
                })
                .catch(error => {
                    console.log('Service Worker registration failed:', error);
                });
        }
    }

    // Dynamic script loading
    loadScript(src) {
        return new Promise((resolve, reject) => {
            // Check if already loaded
            if (document.querySelector(`script[src="${src}"]`)) {
                resolve();
                return;
            }

            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    // Dynamic CSS loading
    loadCSS(href) {
        return new Promise((resolve, reject) => {
            // Check if already loaded
            if (document.querySelector(`link[href="${href}"]`)) {
                resolve();
                return;
            }

            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = href;
            link.onload = resolve;
            link.onerror = reject;
            document.head.appendChild(link);
        });
    }

    // Performance monitoring
    measurePerformance() {
        if ('performance' in window) {
            // Measure page load time
            window.addEventListener('load', () => {
                const navigation = performance.getEntriesByType('navigation')[0];
                const loadTime = navigation.loadEventEnd - navigation.loadEventStart;
                
                console.log(`Page load time: ${loadTime}ms`);
                
                // Send to analytics if available
                if (window.gtag) {
                    gtag('event', 'page_load_time', {
                        value: Math.round(loadTime),
                        custom_parameter: window.location.pathname
                    });
                }
            });

            // Measure largest contentful paint
            new PerformanceObserver((entryList) => {
                const entries = entryList.getEntries();
                const lastEntry = entries[entries.length - 1];
                console.log(`LCP: ${lastEntry.startTime}ms`);
            }).observe({ entryTypes: ['largest-contentful-paint'] });
        }
    }

    // Resource hints
    addResourceHints() {
        const hints = [
            { rel: 'dns-prefetch', href: '//fonts.googleapis.com' },
            { rel: 'dns-prefetch', href: '//cdn.jsdelivr.net' },
            { rel: 'preconnect', href: '//fonts.gstatic.com', crossorigin: true }
        ];

        hints.forEach(hint => {
            const link = document.createElement('link');
            Object.assign(link, hint);
            document.head.appendChild(link);
        });
    }
}

// Initialize optimizer
const performanceOptimizer = new PerformanceOptimizer();

// Start performance measurement
performanceOptimizer.measurePerformance();
performanceOptimizer.addResourceHints();

// Export for global use
window.PerformanceOptimizer = PerformanceOptimizer;