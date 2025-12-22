/**
 * Dashboard JavaScript functionality
 * Handles mobile sidebar and user dropdown menu
 */

(function() {
    'use strict';

    // Mobile Sidebar functionality
    function initMobileSidebar() {
        const mobileMenuButton = document.getElementById('mobile-menu-button');
        const mobileSidebar = document.getElementById('mobile-sidebar');
        const mobileSidebarOverlay = document.getElementById('mobile-sidebar-overlay');
        const closeMobileSidebarBtn = document.getElementById('close-mobile-sidebar');

        if (!mobileMenuButton || !mobileSidebar || !mobileSidebarOverlay) {
            return;
        }

        function openMobileSidebar() {
            mobileSidebar.classList.remove('-translate-x-full');
            mobileSidebarOverlay.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        }

        function closeMobileSidebar() {
            mobileSidebar.classList.add('-translate-x-full');
            mobileSidebarOverlay.classList.add('hidden');
            document.body.style.overflow = '';
        }

        // Make closeMobileSidebar globally accessible for onclick handlers
        window.closeMobileSidebar = closeMobileSidebar;

        // Event listeners
        mobileMenuButton.addEventListener('click', openMobileSidebar);

        if (closeMobileSidebarBtn) {
            closeMobileSidebarBtn.addEventListener('click', closeMobileSidebar);
        }

        mobileSidebarOverlay.addEventListener('click', closeMobileSidebar);
    }

    // User Dropdown functionality
    function initUserDropdown() {
        const dropdown = document.getElementById('user-dropdown-menu');
        const button = document.getElementById('user-menu-button');
        const arrow = document.getElementById('dropdown-arrow');

        if (!dropdown || !button || !arrow) {
            return;
        }

        function toggleUserDropdown() {
            if (dropdown.classList.contains('hidden')) {
                dropdown.classList.remove('hidden', 'opacity-0', 'scale-95');
                dropdown.classList.add('opacity-100', 'scale-100');
                button.setAttribute('aria-expanded', 'true');
                arrow.style.transform = 'rotate(180deg)';
            } else {
                dropdown.classList.add('opacity-0', 'scale-95');
                setTimeout(() => {
                    dropdown.classList.add('hidden');
                }, 200);
                button.setAttribute('aria-expanded', 'false');
                arrow.style.transform = 'rotate(0deg)';
            }
        }

        // Make toggleUserDropdown globally accessible
        window.toggleUserDropdown = toggleUserDropdown;

        // Event listener for button click
        button.addEventListener('click', function(event) {
            event.stopPropagation();
            toggleUserDropdown();
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', function(event) {
            if (!button.contains(event.target) && !dropdown.contains(event.target)) {
                if (!dropdown.classList.contains('hidden')) {
                    dropdown.classList.add('opacity-0', 'scale-95');
                    setTimeout(() => {
                        dropdown.classList.add('hidden');
                    }, 200);
                    button.setAttribute('aria-expanded', 'false');
                    arrow.style.transform = 'rotate(0deg)';
                }
            }
        });
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            initMobileSidebar();
            initUserDropdown();
        });
    } else {
        // DOM is already ready
        initMobileSidebar();
        initUserDropdown();
    }
})();

