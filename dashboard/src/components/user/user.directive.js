(function () {
    'use strict';

    angular
        .module('app.user')
        .directive('gtUser', directiveFunction)
        .controller('UserController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/user/user.html',
            replace: true,
            scope: {},
            controller: 'UserController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['logger'];

    /* @ngInject */
    function ControllerFunction(logger) {
        var vm = this;

        activate();

        function activate() {
            logger.log('Activated User View');
        }
    }
})();
