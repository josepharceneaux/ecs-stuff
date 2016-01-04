(function () {
    'use strict';

    angular.module('app.campaigns')
        .directive('gtEmailCampaigns', directiveFunction)
        .controller('EmailCampaignsController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/campaigns/email-campaigns/email-campaigns.html',
            scope: {
            },
            controller: 'EmailCampaignsController',
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
            logger.log('Activated Email Campaigns View');
        }
    }
})();
