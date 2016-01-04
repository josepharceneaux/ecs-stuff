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
            scope: {
            },
            controller: 'TopnavController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['$state', 'OAuthToken'];

    /* @ngInject */
    function ControllerFunction($state, OAuthToken) {
        var vm = this;
        vm.isCollapsed = true;
        vm.logout = logout;

        init();

        function init() {
            vm.userProfilePicThumbSrc = './images/placeholder/profile.png';
            vm.dashboardScopeOptions = [
                { id: 'sr-java-developers', name: 'Sr Java Developers' },
                { id: 'jr-java-engineers', name: 'Jr Java Engineers' },
                { id: 'developers-in-nevada', name: 'Developers in Nevada' }
            ];
            vm.selectedDashboardScope = vm.dashboardScopeOptions[0];
        }

        function logout() {
            OAuthToken.removeToken();
            $state.go('login');
        }
    }
})();
