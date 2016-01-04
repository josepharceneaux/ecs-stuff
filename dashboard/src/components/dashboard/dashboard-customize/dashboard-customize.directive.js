(function () {
    'use strict';

    angular.module('app.dashboard')
        .directive('gtDashboardCustomize', directiveFunction)
        .controller('DashboardCustomizeController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/dashboard/dashboard-customize/dashboard-customize.html',
            replace: true,
            scope: {
            },
            controller: 'DashboardCustomizeController',
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
            logger.log('Activated Dashboard Customize View');
        }
    }
})();
