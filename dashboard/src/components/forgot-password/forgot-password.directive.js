(function () {
    'use strict';

    angular
        .module('app.forgotPassword')
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
            scope: {},
            controller: 'ForgotPasswordController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['$rootScope', '$state', '$stateParams', 'forgotPasswordService'];

    /* @ngInject */
    function ControllerFunction($rootScope, $state, $stateParams, forgotPasswordService) {
        var vm = this;

        vm.sendForgotPasswordRequest = sendForgotPasswordRequest;

        init();

        function init() {
            if ($stateParams.errorMessage) {
                vm.errorMessage = $stateParams.errorMessage;
            }
        }

        function sendForgotPasswordRequest(username) {
            forgotPasswordService.sendForgotPasswordRequest(username).then(function (response) {
                console.log('forgot password success!:', arguments);
                vm.errorMessage = 'Thanks! If this username belongs to an account, you\'ll receive an email shortly.';
            }, function (response) {
                console.log('forgot password failure:', arguments);
                vm.errorMessage = 'Something went wrong.';
            });
        }
    }
})();
