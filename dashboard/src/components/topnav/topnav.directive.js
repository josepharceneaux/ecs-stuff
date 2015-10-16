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

        function logout() {
            OAuthToken.removeToken();
            $state.go('login');
        }
    }

})();
