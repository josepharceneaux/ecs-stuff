(function () {
    'use strict';

    angular.module('app.pipelines')
        .directive('gtPipelinesNav', directiveFunction)
        .controller('PipelinesNavController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/pipelines/pipelines-nav/pipelines-nav.html',
            replace: true,
            scope: {},
            controller: 'PipelinesNavController',
            controllerAs: 'vm',
            link: linkFunction
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['logger'];

    /* @ngInject */
    function ControllerFunction(logger) {
        var vm = this;

        //vm.isCollapsed = true;
        //vm.menuItems = {
        //    dashboard: {
        //        overview: 'Overview',
        //        customize: 'Customize'
        //    },
        //    pipelines: {
        //        overview: 'Overview',
        //        smartLists: 'Smart Lists',
        //        candidateSearch: 'Candidate Search',
        //        importCandidates: 'Import Candidates'
        //    },
        //    campaigns: {
        //        overview: 'Overview',
        //        emailCampaigns: 'Email Campaigns',
        //        smsCampaigns: 'SMS Campaigns',
        //        socialMediaCampaigns: 'Social Media Campaigns',
        //        contentCampaigns: 'Content Campaigns',
        //        pushNotifications: 'Push Notifications'
        //    },
        //    admin: {
        //        settings: 'Settings'
        //    }
        //};

        activate();

        function activate() {
            logger.log('Activated Pipelines Nav View');
        }
    }

    function linkFunction(scope, elem, attrs) {

        var navParent = $('.js--nav');
        var navItems = $('.js--navItem');

        function navClickout(e) {
            if (!!$(e.target).parents('.view__sidebar').length || $(e.target).is('.view__sidebar')) {
                return;
            }
            return closeNav();
        }

        // -----
        // Helpers
        // -----

        function closeNav() {
            var $activeItem = $('.navigation__item--active');
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
                navItem.deactivate($('.navigation__item--active'));

                $navItem.addClass('navigation__item--active');
            },
            deactivate: function deactivate($navItem) {
                $navItem.removeClass('navigation__item--active')
            }
        };


        // -----
        // Parent Menu
        // -----

        var parentMenu = {
            open: function open() {
                navParent.addClass('view__sidebar--active');
            },
            close: function close() {
                navParent.removeClass('view__sidebar--active');
            },
        };

        // -----
        // Sub Menu
        // -----

        var subMenu = {
            open: function open($subMenu, callback) {
                callback = callback || function () {};

                var $activeMenu = $('.view__sidebar__subNav--active');

                if ($activeMenu.length) {
                    return subMenu.close($activeMenu, function () {
                        return subMenu.open($subMenu);
                    });
                }

                $subMenu
                    .css('display', 'block')
                    .removeClass('view__sidebar__subNav')
                    .addClass('view__sidebar__subNav--active')

                return $.Velocity.animate($subMenu, { opacity: '1' }, {
                    duration: 300,
                    complete: callback()
                });
            },
            close($subMenu, callback) {
                callback = callback || function () {};
                return $.Velocity.animate($subMenu, { opacity: '0' }, {
                    duration: 300,
                    complete: function complete() {
                        $subMenu
                            .removeClass('view__sidebar__subNav--active')
                            .addClass('view__sidebar__subNav')
                            .css('display', 'none')
                            .attr('style', '')

                        callback();
                    }
                });
            }
        };


        // -----
        // Public Methods
        // -----

        function selectSubMenu(element) {
            var $this = element;
            var $selectedMenu = $('.' + $this.data('target'));

            if (!$selectedMenu.length) return false;

            // If this item is already active, close everything
            if ($this.hasClass('navigation__item--active')) {
                return closeNav();
            }

            // If the parent menu hasnt opened yet, open it.
            if (!navParent.hasClass('view__sidebar--active')) {
                parentMenu.open();
            }

            navItem.activate($this);
            subMenu.open($selectedMenu);
        }

        function init() {
            navItems.on('click', function (e) {
                e.preventDefault();
                selectSubMenu($(this));
            });
            $(window).on('resize', closeNav);
        }

        init();

        scope.$on('$destroy', function () {
            navItems.off('click');
            $(window).off('resize', closeNav);
        });
    }
})();
