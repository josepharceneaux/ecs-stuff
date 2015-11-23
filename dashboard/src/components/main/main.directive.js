(function () {
    'use strict';

    angular
        .module('app.main')
        .directive('gtMain', directiveFunction)
        .controller('MainController', ControllerFunction);


    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/main/main.html',
            replace: true,
            scope: {
            },
            controller: 'MainController',
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
