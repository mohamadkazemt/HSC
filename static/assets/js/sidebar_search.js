document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('menu-search-input');
    const menuItems = document.querySelectorAll('#kt_app_sidebar_navs_wrappers .menu-item');

    searchInput.addEventListener('input', function() {
        const searchTerm = searchInput.value.trim().toLowerCase();

        menuItems.forEach(item => {
            const menuItemTitle = item.querySelector('.menu-title');
            const menuHeading = item.querySelector('.menu-heading');
            const menuSub = item.querySelector('.menu-sub');
            const menuSubTitles = item.querySelectorAll('.menu-sub .menu-item .menu-title');

            let itemMatch = false;
            let subMenuMatch = false; // Flag to check if a match is found in sub-menu

            // Check main menu title
            if (menuItemTitle) {
                const title = menuItemTitle.textContent.toLowerCase();
                if (title.includes(searchTerm)) {
                    itemMatch = true;
                }
            }
            // Check menu heading
            else if (menuHeading){
                const headingTitle = menuHeading.textContent.toLowerCase();
                if(headingTitle.includes(searchTerm)){
                    itemMatch = true;
                }
            }
           // Check sub menu titles
            if(menuSubTitles){
               menuSubTitles.forEach(subMenuTitle=>{
                 const subTitleText = subMenuTitle.textContent.toLowerCase();
                   if(subTitleText.includes(searchTerm)){
                     itemMatch = true;
                     subMenuMatch = true; // Set the flag if a sub-menu item matches
                   }
               });
            }

            if(itemMatch) {
               item.style.display = '';
               // If it's a sub-menu match, ensure the parent is open
               if (subMenuMatch && menuSub) {
                   const parentMenuItem = item.closest('.menu-item.menu-accordion');
                   if (parentMenuItem) {
                       parentMenuItem.classList.add('hover'); // Add hover class to visually open
                       parentMenuItem.classList.add('show'); // Add show class to display sub-menu
                       const menuSubElement = parentMenuItem.querySelector('.menu-sub');
                       if (menuSubElement) {
                           menuSubElement.classList.add('show');
                       }
                   }
               }
            } else {
              item.style.display = 'none';
              // If no match, ensure the parent is collapsed
              if (menuSub) {
                  const parentMenuItem = item.closest('.menu-item.menu-accordion');
                  if (parentMenuItem) {
                      parentMenuItem.classList.remove('hover');
                      parentMenuItem.classList.remove('show');
                      const menuSubElement = parentMenuItem.querySelector('.menu-sub');
                      if (menuSubElement) {
                          menuSubElement.classList.remove('show');
                      }
                  }
              }
            }
        });

        // After processing all items, handle the case where the search is cleared
        if (searchTerm === '') {
            menuItems.forEach(item => {
                item.style.display = '';
                const menuSub = item.querySelector('.menu-sub');
                if (menuSub) {
                    const parentMenuItem = item.closest('.menu-item.menu-accordion');
                    if (parentMenuItem) {
                        parentMenuItem.classList.remove('hover');
                        // Only remove 'show' if it wasn't initially open
                        if (!parentMenuItem.classList.contains('here')) {
                            parentMenuItem.classList.remove('show');
                        }
                        const menuSubElement = parentMenuItem.querySelector('.menu-sub');
                        if (menuSubElement && !parentMenuItem.classList.contains('here')) {
                            menuSubElement.classList.remove('show');
                        }
                    }
                }
            });
        }
    });
});