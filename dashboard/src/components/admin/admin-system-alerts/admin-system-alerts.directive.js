(function () {
    'use strict';

    angular.module('app.admin')
        .directive('gtAdminSystemAlerts', directiveFunction)
        .controller('AdminSystemAlertsController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/admin/admin-system-alerts/admin-system-alerts.html',
            replace: true,
            scope: {},
            controller: 'AdminSystemAlertsController',
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
            logger.log('Activated Admin System Alerts View');
        }
    }
})();
