(function () {

    'use strict';

    angular.module('app.campaigns')
        .directive('gtEventCampaigns', directiveFunction)
        .controller('EventCampaignsController', ControllerFunction);


    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/campaigns/event-campaigns/event-campaigns.html',
            scope: {
            },
            controller: 'EventCampaignsController',
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
            logger.log('Activated Event Campaigns View');
        }
    }

})();
