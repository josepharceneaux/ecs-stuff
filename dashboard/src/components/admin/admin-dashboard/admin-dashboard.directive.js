(function () {
    'use strict';

    angular.module('app.admin')
        .directive('gtAdminDashboard', directiveFunction)
        .controller('AdminDashboardController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/admin/admin-dashboard/admin-dashboard.html',
            replace: true,
            scope: {},
            controller: 'AdminDashboardController',
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
            logger.log('Activated Admin Dashboard View');
        }
    }
})();
