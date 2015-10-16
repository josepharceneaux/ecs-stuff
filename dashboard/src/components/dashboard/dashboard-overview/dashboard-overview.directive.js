(function () {

    'use strict';

    angular.module('app.dashboard')
        .directive('gtDashboardOverview', directiveFunction)
        .controller('DashboardOverviewController', ControllerFunction);


    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/dashboard/dashboard-overview/dashboard-overview.html',
            scope: {
            },
            controller: 'DashboardOverviewController',
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
            logger.log('Activated Dashboard Overview View');
        }
    }

})();
