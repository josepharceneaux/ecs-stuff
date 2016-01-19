(function () {
    'use strict';

    angular.module('app.campaigns')
        .directive('gtCampaignsOverview', directiveFunction)
        .controller('CampaignsOverviewController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/campaigns/campaigns-overview/campaigns-overview.html',
            replace: true,
            scope: {},
            controller: 'CampaignsOverviewController',
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
            logger.log('Activated Campaigns Overview View');
        }

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

            vm.pipelineEngagement = {};
            vm.pipelineEngagement.graph = {};
            vm.pipelineEngagement.graph.data = 33;

            vm.itemsPerPageOptions = [
                { value: 5, name: '5 per page' },
                { value: 10, name: '10 per page' },
                { value: 15, name: '15 per page' }
            ];
            vm.campaignsPerPage = vm.itemsPerPageOptions[0].value;

            vm.campaigns = [
                {
                    id: '8a02cb2649e5ea41ec8d110326e67dcd',
                    date: '2015-09-22',
                    name: 'Python developer blast',
                    engagement: '67%',
                    user: 'Jane Quon',
                    type: 'Email',
                    pipeline: 'Python developer'
                },
                {
                    id: 'c8376f01412256a7bec568d412ac0d47',
                    date: '2015-10-11',
                    name: 'Site Engineers meetup',
                    engagement: '23%',
                    user: 'Wally Gibson',
                    type: 'Event',
                    pipeline: 'Site Reliability Engineers'
                },
                {
                    id: 'ca77c211635e6a686f306543270ec470',
                    date: '2015-08-03',
                    name: 'iOS Developer reachout',
                    engagement: '19%',
                    user: 'Tula Martin',
                    type: 'SMS',
                    pipeline: 'iOS Sr. Developer'
                },
                {
                    id: 'a66d5da17fae0c85fc385b2ce9e18355',
                    date: '2015-07-27',
                    name: 'Finance Opportunities',
                    engagement: '72%',
                    user: 'Lee River',
                    type: 'Email',
                    pipeline: 'Finance Analyst'
                },
                {
                    id: '93da1b5b5b984749f476c08a6c8df70a',
                    date: '2015-05-15',
                    name: 'QA Engineers & Automation',
                    engagement: '56%',
                    user: 'Iris Denney',
                    type: 'Social',
                    pipeline: 'Sr. QA Engineer'
                },
                {
                    id: 'e708864855f3bb69c4d9a213b9108b9f',
                    date: '2015-03-02',
                    name: 'Daily Job Alert',
                    engagement: '67%',
                    user: 'Alan Turing',
                    type: 'Email',
                    pipeline: 'Sr. Java Developers in CA'
                }
            ];
        }
    }
})();
