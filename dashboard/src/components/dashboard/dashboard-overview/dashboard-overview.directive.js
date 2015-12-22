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
            replace: true,
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
        var vm = this;

        init();
        activate();

        function init() {
            vm.itemsPerPageOptions = [
                { id: '5', name: '5 per page' },
                { id: '10', name: '10 per page' },
                { id: '15', name: '15 per page' }
            ];
            vm.pipelinesPerPage = vm.itemsPerPageOptions[0];
            vm.campaignsPerPage = vm.itemsPerPageOptions[0];

            vm.heroCharts = [
                { id: 'totalEngagement', name: 'Total Engagement' }
            ];

            vm.heroChartDateRanges = [
                { id: '15d', name: '15d' },
                { id: '30d', name: '30d' },
                { id: '60d', name: '60d' }
            ];
            vm.heroChartDateRange = vm.heroChartDateRanges[0];

            vm.totalCandidates = {};
            vm.totalCandidates.graph = {};
            vm.totalCandidates.graph.data = [
                [
                    { date: '07-01-15', data: 90 },
                    { date: '07-15-15', data: 23 },
                    { date: '08-01-15', data: 71 },
                    { date: '08-15-15', data: 51 },
                    { date: '09-01-15', data: 112 },
                    { date: '09-15-15', data: 39 },
                    { date: '10-01-15', data: 45 },
                    { date: '10-15-15', data: 8 },
                    { date: '11-01-15', data: 88 }
                ],
                [
                    { date: '07-01-15', data: 30 },
                    { date: '07-15-15', data: 133 },
                    { date: '08-01-15', data: 21 },
                    { date: '08-15-15', data: 79 },
                    { date: '09-01-15', data: 52 },
                    { date: '09-15-15', data: 119 },
                    { date: '10-01-15', data: 15 },
                    { date: '10-15-15', data: 80 },
                    { date: '11-01-15', data: 14 }
                ]
            ];

            vm.topContributionsDateRanges = [
                { id: '7-days', name: '7d' },
                { id: '30-days', name: '30d' },
                { id: '60-days', name: '60d' },
                { id: '182-days', name: '6mo' },
                { id: '365-days', name: '1yr' }
            ];
            vm.selectedTopContributionsDateRange = vm.topContributionsDateRanges[0];


            vm.pipelineEngagement = {};
            vm.pipelineEngagement.graph = {};
            vm.pipelineEngagement.graph.data = 33;

            vm.talentPipelinesViewOptions = [
                { id: 'candidate-count-by-pipelines', name: 'Candidate Count by Pipelines' },
                { id: 'candidate-growth-by-pipelines', name: 'Candidate Growth by Pipelines' },
                { id: 'candidate-growth-by-user', name: 'Candidate Growth by User' },
                { id: 'candidate-opt-outs-by-pipelines', name: 'Candidate Opt-Outs by Pipelines' },
                { id: 'engagement-by-pipelines', name: 'Engagement by Pipelines' }
            ];

            vm.activeEngagementViewOptions = [
                { id: 'candidate-count-by-pipelines', name: 'Candidate Count by Pipelines' },
                { id: 'candidate-growth-by-pipelines', name: 'Candidate Growth by Pipelines' },
                { id: 'candidate-growth-by-user', name: 'Candidate Growth by User' },
                { id: 'candidate-opt-outs-by-pipelines', name: 'Candidate Opt-Outs by Pipelines' },
                { id: 'engagement-by-pipelines', name: 'Engagement by Pipelines' }
            ];

            vm.pipelines = [
                {
                    id: 'e708864855f3bb69c4d9a213b9108b9f',
                    name: 'Senior Java Developers in CA',
                    progress: 1
                },
                {
                    id: '912ec803b2ce49e4a541068d495ab570',
                    name: 'Veterans Hiring Initiative',
                    progress: .78
                },
                {
                    id: 'db83bc9caeaa8443b2bcf02d4b55ebee',
                    name: 'Oracle DBAs Overseas',
                    progress: .25
                },
                {
                    id: '22ca8686bfa31a2ae5f55a7f60009e14',
                    name: 'Oracle DBAs Overseas',
                    progress: .5
                }
            ];
        }

        function activate() {
            logger.log('Activated Dashboard Overview View');
        }
    }
})();
