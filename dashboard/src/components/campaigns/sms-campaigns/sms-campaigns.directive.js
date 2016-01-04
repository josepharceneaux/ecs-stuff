(function () {
    'use strict';

    angular.module('app.campaigns')
        .directive('gtSmsCampaigns', directiveFunction)
        .controller('SmsCampaignsController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/campaigns/sms-campaigns/sms-campaigns.html',
            scope: {
            },
            controller: 'SmsCampaignsController',
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
            logger.log('Activated Sms Campaigns View');
        }
    }
})();
