(function () {
    'use strict';

    angular.module('app.styleguide')
        .directive('gtStyleguideDashboard', directiveFunction)
        .controller('StyleguideDashboardController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/styleguide/styleguide-dashboard/styleguide-dashboard.html',
            replace: true,
            scope: {
            },
            controller: 'StyleguideDashboardController',
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

        function init() {
            vm.recipients = [
                { id: 'zack', name: 'Zack' },
                { id: 'greg', name: 'Greg' },
                { id: 'juergen', name: 'Jürgen' },
                { id: 'viktor', name: 'Viktor' }
            ];

            vm.engagementCharts = [
                { id: 'candidate-count-by-pipelines', name: 'Candidate Count by Pipelines' },
                { id: 'candidate-growth-by-pipelines', name: 'Candidate Growth by Pipelines' },
                { id: 'candidate-growth-by-user', name: 'Candidate Growth by User' },
                { id: 'candidate-opt-outs-by-pipelines', name: 'Candidate Opt-Outs by Pipelines' },
                { id: 'engagement-by-pipelines', name: 'Engagement by Pipelines' }
            ];

            vm.campaignTemplates = [
                { id: 'zack', name: 'Template – Zack' },
                { id: 'greg', name: 'Template – Greg' },
                { id: 'juergen', name: 'Template – Jürgen' },
                { id: 'viktor', name: 'Template – Viktor' }
            ];

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

            vm.event = vm.event || {};
            vm.event.startDate = new Date(2015, 11, 1, 17, 0);

            vm.dateFilters = [
                { id: '7-days', name: '7d' },
                { id: '30-days', name: '30d' },
                { id: '60-days', name: '60d' },
                { id: '182-days', name: '6mo' },
                { id: '365-days', name: '1yr' }
            ];
            vm.selectedTopContributionDateFilter = vm.dateFilters[0];

            vm.pipelineYearsXpFilterMin = 0;
            vm.pipelineYearsXpFilterMax = 99;
        }

        function activate() {
            logger.log('Activated Styleguide Dashboard View');
        }
    }
})();
