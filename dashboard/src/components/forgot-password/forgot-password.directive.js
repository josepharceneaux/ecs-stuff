(function () {
    'use strict';

    angular
        .module('app.forgot-password')
        .directive('gtForgotPassword', directiveFunction)
        .controller('ForgotPasswordController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/forgot-password/forgot-password.html',
            replace: true,
            scope: {
            },
            controller: 'ForgotPasswordController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['$rootScope', '$state', '$stateParams'];

    /* @ngInject */
    function ControllerFunction($rootScope, $state, $stateParams) {
        var vm = this;

        vm.email = '';
        vm.errorMessage = '';

        init();

        function init() {
            if ($stateParams.errorMessage) {
                vm.errorMessage = $stateParams.errorMessage;
            }
        }
    }
})();
