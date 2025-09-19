/**
 * Font Loading Manager
 * HSC Project Enhancement - Optimized font loading
 */

class FontLoader {
    constructor() {
        this.loadedFonts = new Set();
        this.init();
    }

    init() {
        // Check if Font Loading API is available
        if ('fonts' in document) {
            this.loadFontsWithAPI();
        } else {
            // Fallback for older browsers
            this.loadFontsFallback();
        }

        // Set up font display optimization
        this.optimizeFontDisplay();
    }

    async loadFontsWithAPI() {
        const fontsToLoad = [
            {
                family: 'Inter',
                weight: '400',
                url: '/static/assets/fonts/Inter-Regular.ttf'
            },
            {
                family: 'Inter',
                weight: '500',
                url: '/static/assets/fonts/Inter-Medium.ttf'
            },
            {
                family: 'Inter',
                weight: '600',
                url: '/static/assets/fonts/Inter-SemiBold.ttf'
            },
            {
                family: 'Inter',
                weight: '700',
                url: '/static/assets/fonts/Inter-Bold.ttf'
            }
        ];

        const loadPromises = fontsToLoad.map(font => this.loadFont(font));
        
        try {
            await Promise.allSettled(loadPromises);
            this.onFontsLoaded();
        } catch (error) {
            console.warn('Some fonts failed to load:', error);
            this.onFontsLoaded(); // Continue anyway
        }
    }

    async loadFont(fontConfig) {
        const { family, weight, url } = fontConfig;
        const fontFace = new FontFace(family, `url(${url})`, { weight });
        
        try {
            const loadedFont = await fontFace.load();
            document.fonts.add(loadedFont);
            this.loadedFonts.add(`${family}-${weight}`);
            
            console.log(`✅ Font loaded: ${family} ${weight}`);
            return loadedFont;
        } catch (error) {
            console.warn(`❌ Failed to load font: ${family} ${weight}`, error);
            throw error;
        }
    }

    loadFontsFallback() {
        // For older browsers, just wait a bit and assume fonts are loaded
        setTimeout(() => {
            this.onFontsLoaded();
        }, 1000);
    }

    onFontsLoaded() {
        // Add class to indicate fonts are ready
        document.documentElement.classList.add('fonts-loaded');
        
        // Trigger custom event
        const event = new CustomEvent('fontsLoaded', {
            detail: { loadedFonts: Array.from(this.loadedFonts) }
        });
        document.dispatchEvent(event);

        // Show previously hidden content
        const fontLoadingElements = document.querySelectorAll('.font-loading');
        fontLoadingElements.forEach(el => {
            el.classList.remove('font-loading');
        });

        console.log('🎉 All fonts loaded successfully!');
    }

    optimizeFontDisplay() {
        // Add font-display: swap to all font-faces
        const style = document.createElement('style');
        style.textContent = `
            @font-face {
                font-display: swap;
            }
        `;
        document.head.appendChild(style);
    }

    // Preload critical fonts
    preloadCriticalFonts() {
        const criticalFonts = [
            '/static/assets/fonts/Inter-Regular.ttf',
            '/static/assets/fonts/Inter-Medium.ttf'
        ];

        criticalFonts.forEach(fontUrl => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.as = 'font';
            link.type = 'font/ttf';
            link.href = fontUrl;
            link.crossOrigin = 'anonymous';
            document.head.appendChild(link);
        });
    }

    // Font loading progress
    getFontLoadingProgress() {
        if ('fonts' in document) {
            const totalFonts = 4; // Number of fonts we're trying to load
            const loadedCount = this.loadedFonts.size;
            return (loadedCount / totalFonts) * 100;
        }
        return 100; // Assume loaded in fallback mode
    }

    // Check if a specific font is loaded
    isFontLoaded(fontFamily, weight = '400') {
        if ('fonts' in document) {
            return document.fonts.check(`${weight} 1em ${fontFamily}`);
        }
        return true; // Assume loaded in fallback mode
    }

    // Wait for specific font to load
    async waitForFont(fontFamily, weight = '400', timeout = 5000) {
        return new Promise((resolve, reject) => {
            const checkFont = () => {
                if (this.isFontLoaded(fontFamily, weight)) {
                    resolve(true);
                }
            };

            // Check immediately
            checkFont();

            // Set up interval checking
            const interval = setInterval(checkFont, 100);

            // Set timeout
            setTimeout(() => {
                clearInterval(interval);
                reject(new Error(`Font ${fontFamily} ${weight} failed to load within ${timeout}ms`));
            }, timeout);
        });
    }
}

// Font loading utilities
const fontLoader = new FontLoader();

// Global font loading functions
window.waitForFont = (family, weight, timeout) => fontLoader.waitForFont(family, weight, timeout);
window.isFontLoaded = (family, weight) => fontLoader.isFontLoaded(family, weight);
window.getFontProgress = () => fontLoader.getFontLoadingProgress();

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Preload critical fonts
    fontLoader.preloadCriticalFonts();
    
    // Show loading progress if needed
    const progressElement = document.querySelector('.font-loading-progress');
    if (progressElement) {
        const updateProgress = () => {
            const progress = fontLoader.getFontLoadingProgress();
            progressElement.style.width = `${progress}%`;
            if (progress < 100) {
                requestAnimationFrame(updateProgress);
            }
        };
        updateProgress();
    }
});

// Listen for font loading completion
document.addEventListener('fontsLoaded', (event) => {
    console.log('Fonts loaded event received:', event.detail);
    
    // Optional: Trigger layout recalculation
    if (window.loadingManager) {
        window.loadingManager.hideGlobalLoading();
    }
    
    // Optional: Update performance metrics
    if (window.performanceOptimizer) {
        window.performanceOptimizer.measurePerformance();
    }
});

// Export for global use
window.FontLoader = FontLoader;
window.fontLoader = fontLoader;