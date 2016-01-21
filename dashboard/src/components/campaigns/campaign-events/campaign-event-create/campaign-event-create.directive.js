(function () {
    'use strict';

    angular.module('app.campaigns')
        .directive('gtCampaignEventCreate', directiveFunction)
        .controller('CampaignEventCreateController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/campaigns/campaign-events/campaign-event-create/campaign-event-create.html',
            replace: true,
            scope: {},
            controller: 'CampaignEventCreateController',
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
            logger.log('Activated Campaign Event Create View');
        }

        function init() {
            vm.eventTypes = [
                { id: 'eventbrite', name: 'Eventbrite' },
                { id: 'eventbrite02', name: 'Eventbrite 01' }
            ];

            vm.smartLists = [
                { id: 'candidate-count-by-pipelines', name: 'Candidate Count by Pipelines' },
                { id: 'candidate-growth-by-pipelines', name: 'Candidate Growth by Pipelines' },
                { id: 'candidate-growth-by-user', name: 'Candidate Growth by User' },
                { id: 'candidate-opt-outs-by-pipelines', name: 'Candidate Opt-Outs by Pipelines' },
                { id: 'engagement-by-pipelines', name: 'Engagement by Pipelines' }
            ];
        }
    }
})();
