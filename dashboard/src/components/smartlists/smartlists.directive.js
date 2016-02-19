(function () {
    'use strict';

    angular.module('app.smartlists')
        .directive('gtSmartlists', directiveFunction)
        .controller('SmartlistsController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/smartlists/smartlists.html',
            replace: true,
            scope: {},
            controller: 'SmartlistsController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['logger','$mdEditDialog', '$q', '$stateParams', 'pipelineService'];

    /* @ngInject */
    function ControllerFunction(logger, $mdEditDialog, $q, $stateParams, pipelineService) {

        var vm = this;
        vm.pipelineId = $stateParams.pipelineId;
        init();
        activate();

        function activate() {
            logger.log('Activated Smartlists View');
        }

        function init() {

            vm.totalCandidates = {
                graph: {}
            };

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

            vm.tableData = {
                filter: {
                    options: {
                        debounce: 500
                    }
                },
                query: {
                    filter: '',
                    order: 'name',
                    limit: 10,
                    page: 1
                },
                smartlists: {
                    count: 0, data: []
                }
            };
            pipelineService.getPipelineSmartlists(vm.pipelineId).then(function(data){
                vm.tableData.smartlists.data = data;
                vm.tableData.smartlists.data.forEach(function(item){
                    item.added_time = moment(item.added_time).toDate();
                });
                vm.tableData.smartlists.count = data.length;
            });
            vm.removeFilter = function () {
                vm.tableData.query.filter = '';

                if (vm.tableData.filter.form.$dirty) {
                    vm.tableData.filter.form.$setPristine();
                }
            };

            vm.logOrder = function (order) {
                console.log('order: ', order);
            };

            vm.logPagination = function (page, limit) {
                console.log('page: ', page);
                console.log('limit: ', limit);
            };
        }
    }
})();
