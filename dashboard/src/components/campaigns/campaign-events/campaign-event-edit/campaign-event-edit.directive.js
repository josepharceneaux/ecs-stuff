(function () {
    'use strict';

    angular.module('app.campaigns')
        .directive('gtCampaignEventEdit', directiveFunction)
        .controller('CampaignEventEditController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/campaigns/campaign-events/campaign-event-edit/campaign-event-edit.html',
            replace: true,
            scope: {},
            controller: 'CampaignEventEditController',
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
            logger.log('Activated Campaign Event Edit View');
        }

        function init() {
            vm.eventTypes = [
                { id: 'eventbrite', name: 'Eventbrite' },
                { id: 'eventbrite02', name: 'Eventbrite 01' }
            ];

            vm.smartlists = [
                { id: 'candidate-count-by-pipelines', name: 'Candidate Count by Pipelines' },
                { id: 'candidate-growth-by-pipelines', name: 'Candidate Growth by Pipelines' },
                { id: 'candidate-growth-by-user', name: 'Candidate Growth by User' },
                { id: 'candidate-opt-outs-by-pipelines', name: 'Candidate Opt-Outs by Pipelines' },
                { id: 'engagement-by-pipelines', name: 'Engagement by Pipelines' }
            ];
        }
    }
})();
