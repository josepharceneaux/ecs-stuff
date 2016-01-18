(function () {
    'use strict';

    angular.module('app.admin')
        .directive('gtAdminEmulate', directiveFunction)
        .controller('AdminEmulateController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/admin/admin-emulate/admin-emulate.html',
            replace: true,
            scope: {},
            controller: 'AdminEmulateController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['$cookies', 'logger'];

    /* @ngInject */
    function ControllerFunction($cookies, logger) {
        var vm = this;

        activate();

        function activate() {
            logger.log('Activated Admin Emulate View');
        }
    }
})();
