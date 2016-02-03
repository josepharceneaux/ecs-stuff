(function () {
    'use strict';

    angular.module('app.pipelines')
        .directive('gtPipelinesOverview', directiveFunction)
        .controller('PipelinesOverviewController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/pipelines/pipelines-overview/pipelines-overview.html',
            replace: true,
            scope: {},
            controller: 'PipelinesOverviewController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['$scope', '$interval', 'logger'];

    /* @ngInject */
    function ControllerFunction($scope, $interval, logger) {
        var vm = this;

        vm.removeFilter = removeFilter;
        vm.logOrder = logOrder;
        vm.logPagination = logPagination;

        init();
        activate();

        function activate() {
            logger.log('Activated Pipelines Overview View');
        }

        function init() {
            vm.pipelineId = 2;

            vm.totalCandidates = {
                graph: {}
            };

            vm.callouts = [
                {
                    name: 'Total Pipelines',
                    tooltip: 'Total number of pipelines in your talent pool',
                    value: '26',
                    change: '<span class="positive">You have 4 pipelines</span>'
                },
                {
                    name: 'Total Candidates',
                    tooltip: 'Total number of candidates in all pipelines',
                    value: '21,683',
                    change: '<span class="positive">(+25%)</span>'
                },
                {
                    name: 'Candidates Added',
                    tooltip: 'Total number of candidates added by your team',
                    value: '559',
                    change: '<span class="negative">(-65%)</span>'
                },
                {
                    name: 'Total Engagement',
                    tooltip: '% of candidates engaged through all of your pipelines',
                    value: '63%',
                    change: '<span class="positive">(+25%)</span>'
                }
            ];

            vm.pipelines = [
                {
                    title: 'Product Management',
                    width: 100,
                    value: '45'
                },
                {
                    title: 'Python',
                    width: 80,
                    value: '35'
                },
                {
                    title: 'Backbone',
                    width: 70,
                    value: '20'
                },
                {
                    title: 'Javascript',
                    width: 65,
                    value: '10'
                },
                {
                    title: 'PHP',
                    width: 50,
                    value: '+16'
                },
                {
                    title: 'Front End Developemnt',
                    width: 50,
                    value: '+16'
                },
                {
                    title: 'UX',
                    width: 50,
                    value: '+16'
                }

            ];

            vm.tableData = {
                filter: {
                    options: {
                        debounce: 500
                    }
                },
                query: {
                    filter: '',
                    order: 'name',
                    limit: 20,
                    page: 1
                },
                pipelines: {
                    count: 20,
                    data: [
                        {
                            id: 1,
                            name: 'Java Developer',
                            candidates: 100,
                            newCandidates: 20,
                            created: new Date('2015-12-17T03:24:00'),
                            smartlists: 4,
                            engagement: '5%',
                            contributors: 'Dean Smith (+20)'
                        }, {
                            id: 2,
                            name: 'Rails Developer',
                            candidates: 870,
                            newCandidates: 12,
                            created: new Date('2015-11-17T03:24:00'),
                            smartlists: 4,
                            engagement: '5%',
                            contributors: 'Dean Smith (+20)'
                        }, {
                            id: 3,
                            name: 'PHP Developer',
                            candidates: 134,
                            newCandidates: 22,
                            created: new Date('2015-10-17T03:24:00'),
                            smartlists: 4,
                            engagement: '5%',
                            contributors: 'Dean Smith (+20)'
                        }, {
                            id: 4,
                            name: 'California based',
                            candidates: 713,
                            newCandidates: 32,
                            created: new Date('2015-02-17T03:24:00'),
                            smartlists: 4,
                            engagement: '5%',
                            contributors: 'Dean Smith (+20)'
                        }, {
                            id: 5,
                            name: 'New York based',
                            candidates: 632,
                            newCandidates: 72,
                            created: new Date('2015-08-17T03:24:00'),
                            smartlists: 4,
                            engagement: '5%',
                            contributors: 'Dean Smith (+20)'
                        }, {
                            id: 6,
                            name: 'Python Developer',
                            candidates: 823,
                            newCandidates: 100,
                            created: new Date('2015-09-12T03:24:00'),
                            smartlists: 4,
                            engagement: '5%',
                            contributors: 'Dean Smith (+20)'
                        }, {
                            id: 7,
                            name: 'Angular Dev',
                            candidates: 189,
                            newCandidates: 34,
                            created: new Date('2015-03-17T03:24:00'),
                            smartlists: 4,
                            engagement: '5%',
                            contributors: 'Dean Smith (+20)'
                        }, {
                            id: 8,
                            name: 'Backbone Dev',
                            candidates: 369,
                            newCandidates: 77,
                            created: new Date('2015-04-17T03:24:00'),
                            smartlists: 4,
                            engagement: '5%',
                            contributors: 'Dean Smith (+20)'
                        }, {
                            id: 9,
                            name: 'Europe based',
                            candidates: 932,
                            newCandidates: 123,
                            created: new Date('2015-06-17T03:24:00'),
                            smartlists: 4,
                            engagement: '5%',
                            contributors: 'Dean Smith (+20)'
                        }, {
                            id: 10,
                            name: 'Canada based',
                            candidates: 453,
                            newCandidates: 62,
                            created: new Date('2015-04-16T03:24:00'),
                            smartlists: 4,
                            engagement: '5%',
                            contributors: 'Dean Smith (+20)'
                        }, {
                            id: 11,
                            name: 'China based',
                            candidates: 824,
                            newCandidates: 103,
                            created: new Date('2015-06-08T03:24:00'),
                            smartlists: 4,
                            engagement: '5%',
                            contributors: 'Dean Smith (+20)'
                        }, {
                            id: 13,
                            name: 'Senior developer',
                            candidates: 253,
                            newCandidates: 29,
                            created: new Date('2015-03-21T03:24:00'),
                            smartlists: 4,
                            engagement: '5%',
                            contributors: 'Dean Smith (+20)'
                        }, {
                            id: 14,
                            name: 'Software Tester',
                            candidates: 521,
                            newCandidates: 64,
                            created: new Date('2015-01-17T03:24:00'),
                            smartlists: 4,
                            engagement: '5%',
                            contributors: 'Dean Smith (+20)'
                        }, {
                            id: 15,
                            name: 'Software designer',
                            candidates: 623,
                            newCandidates: 89,
                            created: new Date('2015-05-18T03:24:00'),
                            smartlists: 4,
                            engagement: '5%',
                            contributors: 'Dean Smith (+20)'
                        }, {
                            id: 16,
                            name: 'Database Engineer',
                            candidates: 354,
                            newCandidates: 65,
                            created: new Date('2015-05-17T03:24:00'),
                            smartlists: 4,
                            engagement: '5%',
                            contributors: 'Dean Smith (+20)'
                        }, {
                            id: 17,
                            name: 'IOS Developer',
                            candidates: 698,
                            newCandidates: 98,
                            created: new Date('2015-09-11T03:24:00'),
                            smartlists: 4,
                            engagement: '5%',
                            contributors: 'Dean Smith (+20)'
                        }, {
                            id: 18,
                            name: 'Android Developer',
                            candidates: 865,
                            newCandidates: 20,
                            created: new Date('2015-06-27T03:24:00'),
                            smartlists: 4,
                            engagement: '5%',
                            contributors: 'Dean Smith (+20)'
                        }, {
                            id: 19,
                            name: 'Business Admin',
                            candidates: 563,
                            newCandidates: 98,
                            created: new Date('2015-08-27T03:24:00'),
                            smartlists: 4,
                            engagement: '5%',
                            contributors: 'Dean Smith (+20)'
                        }, {
                            id: 20,
                            name: 'Trainer',
                            candidates: 951,
                            newCandidates: 156,
                            created: new Date('2015-12-06T03:24:00'),
                            smartlists: 4,
                            engagement: '5%',
                            contributors: 'Dean Smith (+20)'
                        }
                    ]
                }
            };
        }

        function removeFilter() {
            vm.tableData.query.filter = '';

            if (vm.tableData.filter.form.$dirty) {
                vm.tableData.filter.form.$setPristine();
            }
        }

        function logOrder(order) {
            console.log('order: ', order);
        }

        function logPagination(page, limit) {
            console.log('page: ', page);
            console.log('limit: ', limit);
        }
    }
})();
