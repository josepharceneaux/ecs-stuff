(function () {
    'use strict';

    angular
        .module('app.topnav')
        .directive('gtTopnav', directiveFunction)
        .controller('TopnavController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/topnav/topnav.html',
            replace: true,
            scope: {},
            controller: 'TopnavController',
            controllerAs: 'vm',
            link: linkFunction
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['$state', 'OAuth', 'toastr', 'systemAlertsService'];

    /* @ngInject */
    function ControllerFunction($state, OAuth, toastr, systemAlertsService) {
        var vm = this;
        vm.isCollapsed = true;
        vm.logout = logout;
        vm.notifyUser = notifyUser;
        vm.createSystemAlert = createSystemAlert;

        init();

        function init() {
            vm.talentPools = [
                {
                    id: '0cc175b9c0f1b6a831c399e269772661',
                    name: 'Talent Pool 1'
                },
                {
                    id: '187ef4436122d1cc2f40dc2b92f0eba0',
                    name: 'Talent Pool 2'
                },
                {
                    id: '900150983cd24fb0d6963f7d28e17f72',
                    name: 'Talent Pool 3'
                }
            ];
            vm.selectedTalentPool = vm.talentPools[0];

            vm.pipelines = [
                {
                    id: '0cc175b9c0f1b6a831c399e269772661',
                    name: 'Pipeline 1'
                },
                {
                    id: '187ef4436122d1cc2f40dc2b92f0eba0',
                    name: 'Pipeline 2'
                },
                {
                    id: '900150983cd24fb0d6963f7d28e17f72',
                    name: 'Pipeline 3'
                }
            ];

            vm.campaigns = [
                {
                    id: '0cc175b9c0f1b6a831c399e269772661',
                    name: 'Campaign 1'
                },
                {
                    id: '187ef4436122d1cc2f40dc2b92f0eba0',
                    name: 'Campaign 2'
                },
                {
                    id: '900150983cd24fb0d6963f7d28e17f72',
                    name: 'Campaign 3'
                }
            ];
        }

        function logout() {
            OAuth.revokeToken();
            $state.go('login');
        }

        function notifyUser(type) {
            switch (type) {
                case 'success':
                    toastr.success('Hello world!', 'Toastr fun!');
                    break;
                case 'warning':
                    toastr.warning('Your computer is about to explode!', 'Warning');
                    break;
                case 'error':
                    toastr.error('Your credentials are gone', 'Error');
                    break;
                default:
                    toastr.info('We are open today from 10 to 22', 'Information');
            }
        }

        function createSystemAlert() {
            var messages = [
                'Hello world!',
                'Your computer is about to explode!',
                'Your credentials are gone',
                'We are open today from 10 to 22'
            ];

            systemAlertsService.createAlert(messages[Math.round((messages.length - 1) * Math.random())]);
        }


    }

    function linkFunction() {
        var self = {};

        self.navItem   = $('.js--topNavItem');

        let navClickout = function(target, $menu) {
            // console.log(menu.is(target), !!menu.has(target).length)

            if(!!$menu.has(target).length) return;

            return closeSubMenu($menu);
        }

        let openSubMenu = function($menu) {
            setTimeout(function() {
                $('body').bind('click.clickout', function(e) {
                    navClickout(e.target, $menu)
                })
            });

            return $menu.addClass('navigation__item--active')
        }

        let closeSubMenu = function($menu) {
            $('body').unbind('click.clickout')
            return $menu.removeClass('navigation__item--active')
        }

        // -----
        // Public Methods
        // -----

        self.toggleSubMenu = function(element) {
            let $this = element;
            let $subMenu = $this.find('.navigation__subMenu')

            if(!$subMenu.length) return false;

            if($this.hasClass('navigation__item--active')) {
                return closeSubMenu($this)
            } else {
                return openSubMenu($this)
            }
        };


        self.init = function() {
            $(self.navItem).on('click', function(e) {
                e.preventDefault();
                self.toggleSubMenu($(this));
            });
        };

        (function() {
            self.init();
        })();

        return self;
    }
})();
