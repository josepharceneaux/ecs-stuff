(function () {
    'use strict';

    angular
        .module('app.systemAlerts')
        .directive('gtSystemAlerts', directiveFunction)
        .controller('SystemAlertsController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/system-alerts/system-alerts.html',
            replace: true,
            scope: {},
            controller: 'SystemAlertsController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['logger', 'systemAlertsService'];

    /* @ngInject */
    function ControllerFunction(logger, systemAlertsService) {
        var vm = this;

        vm.dismissAlert = dismissAlert;

        init();
        activate();

        function activate() {
            logger.log('Activated System Alerts View');
        }

        function init() {
            vm.alerts = systemAlertsService.getAlerts();
        }

        function dismissAlert(alert) {
            var index;
            if (alert.dismissable) {
                index = vm.alerts.indexOf(alert);
                if (index !== -1) {
                    vm.alerts[index].read = true;
                }
            }
        }
    }
})();
