(function () {
    'use strict';

    angular.module('app.campaigns')
        .directive('gtContentCampaigns', directiveFunction)
        .controller('ContentCampaignsController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/campaigns/content-campaigns/content-campaigns.html',
            scope: {
            },
            controller: 'ContentCampaignsController',
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
            logger.log('Activated Content Campaigns View');
        }
    }
})();
