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
    ControllerFunction.$inject = ['systemAlertsService'];

    /* @ngInject */
    function ControllerFunction(systemAlertsService) {
        var vm = this;

        vm.dismissAlert = dismissAlert;

        init();

        function init() {
            systemAlertsService.getAlerts().then(function (response) {
                vm.alerts = response.alerts;
            });
        }

        function dismissAlert(alert) {
            var index = vm.alerts.indexOf(alert);
            if (index !== -1) {
                vm.alerts.splice(index, 1);
            }
        }
    }
})();
