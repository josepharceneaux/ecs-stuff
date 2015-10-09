(function () {

    'use strict';

    angular.module('app.campaigns')
        .directive('gtCampaignsOverview', directiveFunction)
        .controller('CampaignsOverviewController', ControllerFunction);


    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/campaigns/campaigns-overview/campaigns-overview.html',
            scope: {
            },
            controller: 'CampaignsOverviewController',
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
            logger.log('Activated Campaigns Overview View');
        }
    }

})();
