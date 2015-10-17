(function () {
    'use strict';

    angular
        .module('app.login')
        .directive('gtLogin', directiveFunction)
        .controller('LoginController', ControllerFunction);


    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/login/login.html',
            scope: {
            },
            controller: 'LoginController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['$rootScope', '$state', '$stateParams', 'OAuth'];

    /* @ngInject */
    function ControllerFunction($rootScope, $state, $stateParams, OAuth) {
        var vm = this;

        vm.username = '';
        vm.password = '';
        vm.errorMessage = '';
        vm.login = login;

        init();

        function init() {
            if ($stateParams.errorMessage) {
                vm.errorMessage = $stateParams.errorMessage;
            }
        }

        function login() {
            OAuth.getAccessToken({
                username: vm.username,
                password: vm.password
            }).then(function() {
                if (angular.isDefined($rootScope.redirectTo)) {
                    $state.go($rootScope.redirectTo.state, $rootScope.redirectTo.params);
                } else {
                    $state.go('dashboard');
                }
            }, function() {
                vm.errorMessage = 'Authentication failed.';
            });
        }
    }

})();