// -------------------------------------
//   Candidate Growth Graph
//   ->
// -------------------------------------

(function () {
    'use strict';

    angular
        .module('app.core')
        .directive('gtCandidateGrowthGraph', directiveFunction)
        .controller('CandidateGrowthGraphController', ControllerFunction)

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'AE',
            require: ['gtCandidateGrowthGraph'],
            templateUrl: 'core/modules/d3/candidate-growth-graph/candidate-growth-graph.html',
            replace: true,
            scope: {
                pipelineId: '='
            },
            controller: 'CandidateGrowthGraphController',
            controllerAs: 'candidateGrowthGraph',
            bindToController: true,
            link: linkFunction
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['candidateGrowthService'];

    /* @ngInject */
    function ControllerFunction(candidateGrowthService) {
        var vm = this;

        var series = [{
            name: 'Candidates Added',
            data: []
        }];

        var statRequest;
        var toDate = new Date(2016, 4, 3); // test, "today" = May 3, 2016
        var fromDate = new Date(toDate.getTime());

        vm.onDateRangeChange = onDateRangeChange;
        vm.updateSeries = updateSeries;

        init();

        function init() {
            vm.title = 'Candidate Growth';
            vm.dateRangeOptions = [7, 30, 60, 90];
            vm.dateRange = vm.dateRangeOptions[1];
            vm.config = {
                series: series,
                func: function (chart) {
                    vm.chart = chart;
                },
                loading: true
            };
            updateSeries();
        }

        function updateSeries() {
            var numExpectedDataPoints = getNumExpectedDataPoints(vm.dateRange);
            var dateInterval = getDateInterval(vm.dateRange, numExpectedDataPoints);
            var pointStart = fromDate.getTime();
            var pointInterval = daysToMilliseconds(dateInterval);
            var params;

            fromDate = new Date(toDate.getTime());
            fromDate.setDate(fromDate.getDate() - vm.dateRange);

            params = {
                from_date: fromDate,
                to_date: toDate,
                interval: dateInterval
            };

            // cancel any pending requests, to guarantee that only the most recent request
            // ends up update the graph data.
            if (statRequest) {
                statRequest.cancel();
                statRequest = null;
            }

            vm.config.loading = true;

            statRequest = candidateGrowthService.getPipelineStats(vm.pipelineId, params);

            statRequest.then(function (stats) {
                var data;

                vm.config.loading = false;

                data = stats.map(function (stat) {
                    return stat.total_number_of_candidates;
                });

                // buffer beginning of array with 0s until it meets the expected
                // number of data points
                while (data.length < numExpectedDataPoints) {
                    data.unshift(0);
                }

                // changing through highcharts-ng config will animate the axis changes
                //series[0].pointStart = pointStart;
                //series[0].pointInterval = pointInterval;
                //series[0].data = data;

                // update() = no animation
                vm.chart.series[0].update({
                    pointStart: pointStart,
                    pointInterval: pointInterval,
                    data: data
                });
            });
        }

        function onDateRangeChange(dateRange) {
            vm.dateRange = dateRange;
            updateSeries();
        }

        function getDateInterval(dateRange, numExpectedDataPoints) {
            return Math.floor(dateRange / numExpectedDataPoints);
        }
        function daysToMilliseconds(days) {
            var day = 24 * 60 * 60 * 1000;
            return day * days;
        }

        function getNumExpectedDataPoints(dateRange) {
            if (dateRange === 7) return 7;
            else return 15;
        }
    }

    function linkFunction(scope, elem, attrs, ctrls) {
        //
    }

})();
