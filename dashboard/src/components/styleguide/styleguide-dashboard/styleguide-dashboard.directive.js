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
            scope: {},
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

            vm.newCandidates = {};
            vm.newCandidates.graph = {};
            vm.newCandidates.graph.data = [
                { date: '10-07-15', data: 10 },
                { date: '10-08-15', data: 11 },
                { date: '10-09-15', data: 13 },
                { date: '10-10-15', data: 15 },
                { date: '10-11-15', data: 10 },
                { date: '10-12-15', data: 7 },
                { date: '10-13-15', data: 8 },
                { date: '10-14-15', data: 10 },
                { date: '10-15-15', data: 10 },
                { date: '10-16-15', data: 14 },
                { date: '10-17-15', data: 15 },
                { date: '10-18-15', data: 10 }
            ];

            vm.pipelineEngagement = {};
            vm.pipelineEngagement.graph = {};
            vm.pipelineEngagement.graph.data = 33;

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

            vm.smartlists = [
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

            vm.topSkills = [
                { name: 'Automatic Data Processing' },
                { name: 'Angular JS' },
                { name: 'Hadoop' },
                { name: 'HTML5' },
                { name: 'Apache Jackrabbit' },
                { name: 'Linux' },
                { name: 'Production Management' },
                { name: 'Software Troubleshooting' },
                { name: 'Sybase Unwired Platform' },
                { name: 'Location-Based Services' },
                { name: 'DevOps' },
                { name: 'LTX Credence' }
            ];

            vm.topLocations = [
                { formattedLocation: 'Portland, OR' },
                { formattedLocation: 'Detroit, MI' },
                { formattedLocation: 'Orlando, FL' },
                { formattedLocation: 'Santa Cruz, CA' },
                { formattedLocation: 'Miami, FL' },
                { formattedLocation: 'Seattle, WA' },
                { formattedLocation: 'Olympia, WA' },
                { formattedLocation: 'Dallas, TX' },
                { formattedLocation: 'Denver, CO' }
            ];

            vm.topSites = [
                { location: 'Seattle, WA' },
                { location: 'Olympia, WA' },
                { location: 'Dallas, TX' },
                { location: 'Portland, OR' },
                { location: 'Detroit, MI' },
                { location: 'Orlando, FL' },
                { location: 'Santa Cruz, CA' },
                { location: 'Miami, FL' },
                { location: 'Denver, CO' }
            ];

            vm.topReferrals = [
                { location: 'Miami, FL' },
                { location: 'Seattle, WA' },
                { location: 'Olympia, WA' },
                { location: 'Dallas, TX' },
                { location: 'Denver, CO' },
                { location: 'Portland, OR' },
                { location: 'Detroit, MI' },
                { location: 'Orlando, FL' },
                { location: 'Santa Cruz, CA' }
            ];
        }

        function activate() {
            logger.log('Activated Styleguide Dashboard View');
        }
    }
})();
