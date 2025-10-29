// Theme + layout controller (Alpine-compatible)
(function () {
  const STORAGE_KEY = 'theme';
  const docEl = document.documentElement;

  function getStoredTheme() {
    try { return localStorage.getItem(STORAGE_KEY); } catch (_) { return null; }
  }
  function storeTheme(val) {
    try { localStorage.setItem(STORAGE_KEY, val); } catch (_) {}
  }
  function systemPrefersDark() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  }
  function applyTheme(theme) {
    const isDark = theme === 'dark';
    docEl.classList.toggle('dark', isDark);
    docEl.setAttribute('data-theme', theme);
  }

  window.layout = function () {
    return {
      sidebarOpen: false,
      isDark: false,
      initTheme() {
        const saved = getStoredTheme();
        const theme = saved ? saved : (systemPrefersDark() ? 'dark' : 'light');
        this.isDark = theme === 'dark';
        applyTheme(theme);
      },
      toggleTheme() {
        this.isDark = !this.isDark;
        const theme = this.isDark ? 'dark' : 'light';
        storeTheme(theme);
        applyTheme(theme);
      },
      toggleSidebar() { this.sidebarOpen = !this.sidebarOpen; },
      closeSidebar() { this.sidebarOpen = false; }
    };
  };
})();
