(function () {
    'use strict';

    angular.module('app.user')
        .directive('gtUserAccount', directiveFunction)
        .controller('UserAccountController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/user/user-account/user-account.html',
            replace: true,
            scope: {},
            controller: 'UserAccountController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['logger'];

    /* @ngInject */
    function ControllerFunction(logger) {
        var vm = this;

        init();
        activate();

        function activate() {
            logger.log('Activated User Account View');
        }

        function init() {
            //
        }
    }
})();
