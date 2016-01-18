(function () {
    'use strict';

    angular
        .module('app.resetPassword')
        .directive('gtResetPassword', directiveFunction)
        .controller('ResetPasswordController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/reset-password/reset-password.html',
            replace: true,
            scope: {},
            controller: 'ResetPasswordController',
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
