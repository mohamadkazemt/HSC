/**
 * CSS and JS Minification Utility
 * HSC Project Enhancement
 */

class AssetMinifier {
    constructor() {
        this.init();
    }

    init() {
        // Only run in production or when explicitly requested
        if (this.shouldMinify()) {
            this.minifyCSS();
            this.minifyJS();
            this.optimizeImages();
            this.setupResourceBundling();
        }
    }

    shouldMinify() {
        // Check if we're in production mode or debug is false
        return (typeof window.DEBUG === 'undefined' || !window.DEBUG) && 
               window.location.hostname !== 'localhost' && 
               window.location.hostname !== '127.0.0.1' || 
               localStorage.getItem('forceMinify') === 'true';
    }

    // CSS Minification
    minifyCSS() {
        const styles = document.querySelectorAll('style');
        styles.forEach(style => {
            if (style.textContent && !style.hasAttribute('data-minified')) {
                style.textContent = this.minifyCSSText(style.textContent);
                style.setAttribute('data-minified', 'true');
            }
        });

        // Process external stylesheets if they're inline
        this.processInlineStyles();
    }

    minifyCSSText(css) {
        return css
            // Remove comments
            .replace(/\/\*[\s\S]*?\*\//g, '')
            // Remove unnecessary whitespace
            .replace(/\s+/g, ' ')
            // Remove spaces around certain characters
            .replace(/\s*([{}:;,>+~])\s*/g, '$1')
            // Remove trailing semicolons
            .replace(/;}/g, '}')
            // Remove leading/trailing whitespace
            .trim();
    }

    processInlineStyles() {
        const elements = document.querySelectorAll('[style]');
        elements.forEach(el => {
            const style = el.getAttribute('style');
            if (style) {
                el.setAttribute('style', this.minifyCSSText(style));
            }
        });
    }

    // JS Minification (basic)
    minifyJS() {
        const scripts = document.querySelectorAll('script:not([src])');
        scripts.forEach(script => {
            if (script.textContent && !script.hasAttribute('data-minified')) {
                script.textContent = this.minifyJSText(script.textContent);
                script.setAttribute('data-minified', 'true');
            }
        });
    }

    minifyJSText(js) {
        return js
            // Remove single-line comments (but be careful with URLs)
            .replace(/\/\/.*$/gm, '')
            // Remove multi-line comments
            .replace(/\/\*[\s\S]*?\*\//g, '')
            // Remove unnecessary whitespace
            .replace(/\s+/g, ' ')
            // Remove spaces around operators and punctuation
            .replace(/\s*([{}()[\];,=+\-*/<>!&|?:])\s*/g, '$1')
            // Remove trailing semicolons before }
            .replace(/;}/g, '}')
            .trim();
    }

    // Image optimization
    optimizeImages() {
        // Convert images to WebP if supported
        if (this.supportsWebP()) {
            this.convertImagesToWebP();
        }
        
        // Apply compression techniques
        this.compressImages();
    }

    supportsWebP() {
        const canvas = document.createElement('canvas');
        return canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
    }

    convertImagesToWebP() {
        const images = document.querySelectorAll('img[src]');
        images.forEach(img => {
            // Only process local images
            if (!this.isExternalLink(img.src) && 
                !img.src.includes('.webp') && 
                !img.hasAttribute('data-webp-processed') &&
                /\.(jpg|jpeg|png)$/i.test(img.src)) {
                
                const webpSrc = img.src.replace(/\.(jpg|jpeg|png)$/i, '.webp');
                
                // Test if WebP version exists
                this.testImage(webpSrc).then(exists => {
                    if (exists) {
                        img.src = webpSrc;
                    }
                }).catch(() => {
                    // Silently fail for missing WebP images
                });
                
                img.setAttribute('data-webp-processed', 'true');
            }
        });
    }

    testImage(src) {
        return new Promise(resolve => {
            const img = new Image();
            img.onload = () => resolve(true);
            img.onerror = () => resolve(false);
            img.src = src;
        });
    }

    compressImages() {
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            if (!img.hasAttribute('data-compressed')) {
                // Add loading optimization
                img.setAttribute('loading', 'lazy');
                img.setAttribute('decoding', 'async');
                
                // Set appropriate sizes if not set
                if (!img.hasAttribute('sizes') && img.hasAttribute('srcset')) {
                    img.setAttribute('sizes', '(max-width: 768px) 100vw, 50vw');
                }
                
                img.setAttribute('data-compressed', 'true');
            }
        });
    }

    // Resource bundling simulation
    setupResourceBundling() {
        this.bundleCSS();
        this.bundleJS();
        this.setupResourceHints();
    }

    bundleCSS() {
        const links = document.querySelectorAll('link[rel="stylesheet"]:not([data-bundled])');
        const criticalCSS = [];
        const nonCriticalCSS = [];
        
        links.forEach(link => {
            const href = link.href;
            
            // Skip external links (CDN, Google Fonts, etc.)
            if (this.isExternalLink(href)) {
                link.setAttribute('data-bundled', 'true');
                return;
            }
            
            // Categorize CSS as critical or non-critical
            if (this.isCriticalCSS(href)) {
                criticalCSS.push(link);
            } else {
                nonCriticalCSS.push(link);
            }
            
            link.setAttribute('data-bundled', 'true');
        });

        // Load non-critical CSS asynchronously
        this.loadNonCriticalCSS(nonCriticalCSS);
    }

    isExternalLink(href) {
        // Check if link is external (different domain)
        try {
            const url = new URL(href);
            return url.origin !== window.location.origin;
        } catch (e) {
            // If URL parsing fails, assume it's internal
            return false;
        }
    }

    isCriticalCSS(href) {
        const criticalPatterns = [
            'style.bundle.css',
            'plugins.bundle.css',
            'bootstrap',
            'critical'
        ];
        
        return criticalPatterns.some(pattern => href.includes(pattern));
    }

    loadNonCriticalCSS(links) {
        links.forEach(link => {
            // Convert to non-blocking load
            link.media = 'print';
            link.onload = function() {
                this.media = 'all';
            };
        });
    }

    bundleJS() {
        const scripts = document.querySelectorAll('script[src]:not([data-bundled])');
        const criticalJS = [];
        const nonCriticalJS = [];
        
        scripts.forEach(script => {
            const src = script.src;
            
            if (this.isCriticalJS(src)) {
                criticalJS.push(script);
            } else {
                nonCriticalJS.push(script);
                
                // Make non-critical JS async
                if (!script.hasAttribute('async') && !script.hasAttribute('defer')) {
                    script.setAttribute('defer', 'true');
                }
            }
            
            script.setAttribute('data-bundled', 'true');
        });
    }

    isCriticalJS(src) {
        const criticalPatterns = [
            'plugins.bundle.js',
            'scripts.bundle.js',
            'jquery',
            'bootstrap'
        ];
        
        return criticalPatterns.some(pattern => src.includes(pattern));
    }

    setupResourceHints() {
        // Add preload for critical resources
        this.preloadCriticalResources();
        
        // Add prefetch for likely needed resources
        this.prefetchResources();
        
        // Add preconnect for external domains
        this.preconnectExternalDomains();
    }

    preloadCriticalResources() {
        const criticalResources = [
            { href: '/static/assets/css/style.bundle.css', as: 'style' },
            { href: '/static/assets/js/scripts.bundle.js', as: 'script' },
            { href: '/static/assets/plugins/global/plugins.bundle.css', as: 'style' }
        ];

        criticalResources.forEach(resource => {
            if (!document.querySelector(`link[href="${resource.href}"][rel="preload"]`)) {
                const link = document.createElement('link');
                link.rel = 'preload';
                link.href = resource.href;
                link.as = resource.as;
                if (resource.as === 'style') {
                    link.onload = function() {
                        this.onload = null;
                        this.rel = 'stylesheet';
                    };
                }
                document.head.appendChild(link);
            }
        });
    }

    prefetchResources() {
        const prefetchResources = [
            '/dashboard/',
            '/core/logs/',
            '/accounts/profile/'
        ];

        prefetchResources.forEach(href => {
            if (!document.querySelector(`link[href="${href}"][rel="prefetch"]`)) {
                const link = document.createElement('link');
                link.rel = 'prefetch';
                link.href = href;
                link.onerror = () => {
                    // Silently handle missing resources
                    link.remove();
                };
                document.head.appendChild(link);
            }
        });
    }

    preconnectExternalDomains() {
        const domains = [
            'https://fonts.googleapis.com',
            'https://fonts.gstatic.com',
            'https://cdn.jsdelivr.net'
        ];

        domains.forEach(domain => {
            if (!document.querySelector(`link[href="${domain}"][rel="preconnect"]`)) {
                const link = document.createElement('link');
                link.rel = 'preconnect';
                link.href = domain;
                link.crossOrigin = 'anonymous';
                document.head.appendChild(link);
            }
        });
    }

    // Performance monitoring
    measureOptimizationImpact() {
        if ('performance' in window) {
            // Measure resource loading times
            const resources = performance.getEntriesByType('resource');
            const cssResources = resources.filter(r => r.name.includes('.css'));
            const jsResources = resources.filter(r => r.name.includes('.js'));
            
            console.log('CSS Resources:', cssResources.length, 
                       'Average load time:', this.averageLoadTime(cssResources));
            console.log('JS Resources:', jsResources.length, 
                       'Average load time:', this.averageLoadTime(jsResources));
        }
    }

    averageLoadTime(resources) {
        if (resources.length === 0) return 0;
        const totalTime = resources.reduce((sum, resource) => {
            return sum + (resource.responseEnd - resource.requestStart);
        }, 0);
        return Math.round(totalTime / resources.length);
    }

    // Manual controls for testing
    static enableMinification() {
        localStorage.setItem('forceMinify', 'true');
        location.reload();
    }

    static disableMinification() {
        localStorage.removeItem('forceMinify');
        location.reload();
    }

    static measurePerformance() {
        if (window.assetMinifier) {
            window.assetMinifier.measureOptimizationImpact();
        }
    }
}

// Initialize the minifier
const assetMinifier = new AssetMinifier();

// Make it globally available
window.assetMinifier = assetMinifier;
window.AssetMinifier = AssetMinifier;

// Measure performance after page load
window.addEventListener('load', () => {
    setTimeout(() => {
        assetMinifier.measureOptimizationImpact();
    }, 1000);
});