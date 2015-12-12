(function () {
    'use strict';

    angular
        .module('app.sidenav')
        .directive('gtSidenav', directiveFunction)
        .controller('SidenavController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/sidenav/sidenav.html',
            replace: true,
            scope: {
            },
            controller: 'SidenavController',
            controllerAs: 'vm',
            link: linkFunction
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['$state'];

    /* @ngInject */
    function ControllerFunction($state) {
        var vm = this;
        vm.isCollapsed = true;
        vm.state = $state;
        vm.menuItems = {
            dashboard: {
                overview: 'Overview',
                customize: 'Customize'
            },
            pipelines: {
                overview: 'Overview',
                smartLists: 'Smart Lists',
                candidateSearch: 'Candidate Search',
                importCandidates: 'Import Candidates'
            },
            campaigns: {
                overview: 'Overview',
                emailCampaigns: 'Email Campaigns',
                smsCampaigns: 'SMS Campaigns',
                socialMediaCampaigns: 'Social Media Campaigns',
                contentCampaigns: 'Content Campaigns',
                pushNotifications: 'Push Notifications'
            },
            admin: {
                settings: 'Settings'
            }
        };
    }

    function linkFunction(scope, elem, attrs) {

        var navParent = $('.js--nav');
        var navItems  = $('.js--navItem');

        function navClickout(e) {
            if (!!$(e.target).parents('.view__sidebar').length ||
                $(e.target).is('.view__sidebar')) return;

            return closeNav();
        }

        // -----
        // Helpers
        // -----

        function closeNav() {
            var $activeItem = $('.view__sidebar__navItem--active');
            var $activeMenu = $('.view__sidebar__subNav--active');

            navItem.deactivate($activeItem);
            parentMenu.close(navParent);
            subMenu.close($activeMenu);

            $('body').unbind('click.clickout');
        }

        // -----
        // Nav Link
        // -----

        var navItem = {
            activate: function activate($navItem) {
                navItem.deactivate($('.view__sidebar__navItem--active'));

                $navItem
                    .removeClass('view__sidebar__navItem')
                    .addClass('view__sidebar__navItem--active');
            },
            deactivate: function deactivate($navItem) {
                $navItem
                    .removeClass('view__sidebar__navItem--active')
                    .addClass('view__sidebar__navItem');
            }
        }


        // -----
        // Parent Menu
        // -----

        var parentMenu = {
            open: function open($navParent) {
                $navParent
                    .removeClass('view__sidebar__navParent')
                    .addClass('view__sidebar__navParent--active');

                setTimeout(function () {
                    $('body').on('click.clickout', navClickout);
                });
            },
            close: function close($navParent) {
                $navParent
                    .removeClass('view__sidebar__navParent--active')
                    .addClass('view__sidebar__navParent');
            },
        };

        // -----
        // Sub Menu
        // -----

        var subMenu = {
            open: function open($subMenu, callback) {
                var $activeMenu = $('.view__sidebar__subNav--active');

                if ($activeMenu.length) {
                    return subMenu.close($activeMenu, function () {
                        subMenu.open($subMenu)
                    });
                }

                $subMenu
                    .css('display', 'block')
                    .removeClass('view__sidebar__subNav')
                    .addClass('view__sidebar__subNav--active');

                return $.Velocity.animate($subMenu, { opacity: '1' }, {
                    duration: 300,
                    complete: (callback || (function () {}))()
                });
            },
            close: function close($subMenu, callback) {
                return $.Velocity.animate($subMenu, { opacity: '0' }, {
                    duration: 300,
                    complete: function complete() {
                        $subMenu
                            .removeClass('view__sidebar__subNav--active')
                            .addClass('view__sidebar__subNav')
                            .css('display', 'none')
                            .attr('style', '');

                        (callback || function () {})();
                    }
                });
            }
        };


        // -----
        // Public Methods
        // -----

        function selectSubMenu(element) {
            var $this                 = element;
            var $selectedMenu = $('.' + $this.data('target'));

            if (!$selectedMenu.length) return false;

            // If this item is already active, close everything
            if ($this.hasClass('view__sidebar__navItem--active')) {
                return closeNav();
            }

            // If the parent menu hasnt opened yet, open it.
            if (!navParent.hasClass('view__sidebar__navParent--active')) {
                parentMenu.open(navParent);
            }

            navItem.activate($this);
            subMenu.open($selectedMenu);
        };


        function init() {
            navItems.on('click', function (e) {
                e.preventDefault();
                selectSubMenu($(this));
            });
        };

        init();

        scope.$on('$destroy', function () {
            navItems.off('click');
        });
    }
})();
