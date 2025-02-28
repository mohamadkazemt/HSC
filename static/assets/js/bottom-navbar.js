document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const formsMenuTrigger = document.getElementById('forms-menu-trigger');
    const formsMenu = document.getElementById('forms-menu');
    const notificationsToggle = document.getElementById('notifications-toggle');
    const notificationsMenu = document.getElementById('notifications-menu');
    const messagesToggle = document.getElementById('messages-toggle');
    const messagesMenu = document.getElementById('messages-menu');
    const profileToggle = document.getElementById('profile-toggle');
    const profileMenu = document.getElementById('profile-menu');
    const overlay = document.querySelector('.menu-overlay');
    
    let activeMenu = null;

    // Function to close all menus
    function closeAllMenus() {
        [formsMenu, notificationsMenu, messagesMenu, profileMenu].forEach(menu => {
            if (menu) {
                menu.classList.remove('show');
            }
        });
        overlay.classList.remove('show');
        
        // Reset plus icon rotation
        if (formsMenuTrigger) {
            formsMenuTrigger.querySelector('.menu-icon i').style.transform = 'rotate(0deg)';
        }
        
        activeMenu = null;
    }

    // Function to toggle specific menu
    function toggleMenu(menu, button) {
        if (activeMenu === menu) {
            closeAllMenus();
        } else {
            closeAllMenus();
            menu.classList.add('show');
            overlay.classList.add('show');
            activeMenu = menu;
            
            // Rotate plus icon if it's the forms menu
            if (menu === formsMenu && button === formsMenuTrigger) {
                button.querySelector('.menu-icon i').style.transform = 'rotate(45deg)';
            }
        }
    }

    // Event Listeners
    if (formsMenuTrigger) {
        formsMenuTrigger.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            toggleMenu(formsMenu, this);
        });
    }

    if (notificationsToggle) {
        notificationsToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            toggleMenu(notificationsMenu, this);
        });
    }

    if (messagesToggle) {
        messagesToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            toggleMenu(messagesMenu, this);
        });
    }

    if (profileToggle) {
        profileToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            toggleMenu(profileMenu, this);
        });
    }

    // Close menus when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.bottom-navbar') && 
            !e.target.closest('.menu-sub-dropdown') && 
            !e.target.closest('.forms-menu')) {
            closeAllMenus();
        }
    });

    // Close menus when clicking overlay
    if (overlay) {
        overlay.addEventListener('click', closeAllMenus);
    }

    // Handle touch events for swipe down to close
    let touchStartY = 0;
    let touchEndY = 0;

    document.addEventListener('touchstart', function(e) {
        touchStartY = e.touches[0].clientY;
    }, { passive: true });

    document.addEventListener('touchmove', function(e) {
        if (!activeMenu) return;
        
        touchEndY = e.touches[0].clientY;
        if (touchStartY - touchEndY < -50) { // Swipe down
            closeAllMenus();
        }
    }, { passive: true });

    // Close menus on scroll
    window.addEventListener('scroll', function() {
        if (activeMenu) {
            closeAllMenus();
        }
    }, { passive: true });
}); 