(function () {
    'use strict';

    angular.module('app.admin')
        .directive('gtAdmin', directiveFunction)
        .controller('AdminController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/admin/admin.html',
            replace: true,
            scope: {
            },
            controller: 'AdminController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['logger'];

    /* @ngInject */
    function ControllerFunction(logger) {

        activate();

        function activate() {
            logger.log('Activated Admin View');
        }
    }
})();
