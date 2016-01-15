(function () {
    'use strict';

    angular.module('app.campaigns')
        .directive('gtCampaignEventDetail', directiveFunction)
        .controller('CampaignEventDetailController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/campaigns/campaign-events/campaign-event-detail/campaign-event-detail.html',
            scope: {
            },
            controller: 'CampaignEventDetailController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['logger'];

    /* @ngInject */
    function ControllerFunction(logger) {
        var vm = this;

        init();
        activate();

        function activate() {
            logger.log('Activated Campaign Event Detail View');
        }

        function init() {
            //
        }
    }
})();
