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

        var dataSetLast24Hours;
        var dataSetLast90Days;

        vm.redrawChart = redrawChart;
        vm.updateChart = updateChart;
        vm.removeFilter = removeFilter;
        vm.logOrder = logOrder;
        vm.logPagination = logPagination;

        init();
        activate();

        function activate() {
            logger.log('Activated Pipelines Overview View');
        }

        function init() {
            // mock data: candidate growth
            // by "hour", last day
            dataSetLast24Hours = [1, 0, 0, 0,
                                  0, 2, 5, 8,
                                  10, 3, 0, 3,
                                  13, 2, 3, 3,
                                  5, 6, 10, 12,
                                  8, 15, 20, 4];

            // by "day", last 90 days
            dataSetLast90Days = [48, 97, 38, 63, 45, 96, 47, 14, 45, 46,
                                 29, 21, 16, 32, 25, 109, 93, 27, 50, 96,
                                 46, 76, 72, 68, 32, 43, 67, 31, 117, 98,
                                 110, 59, 76, 36, 2, 50, 81, 89, 27, 26,
                                 118, 86, 29, 35, 61, 45, 76, 64, 135, 58,
                                 62, 100, 39, 77, 48, 108, 124, 93, 17, 26,
                                 21, 52, 54, 19, 41, 12, 29, 59, 29, 106,
                                 54, 25, 26, 13, 32, 51, 41, 82, 34, 153,
                                 83, 46, 50, 70, 87, 33, 57, 40, 38, 133];

            vm.chartFilters = {};
            vm.daysFilterOptions = [7, 30, 60, 90];
            vm.chartFilters.daysBack = vm.daysFilterOptions[1];

            vm.chartConfig = {
                options: {
                    chart: {
                        type: 'area',
                        backgroundColor: null,
                        spacingLeft: 40,
                        spacingRight: 40,
                        spacingTop: 50,
                        style: {
                            fontFamily: '"Roboto", "Helvetica Neue", Helvetica, Arial, sans-serif',
                            fontWeight: 300
                        }
                    },
                    credits: {
                        enabled: false
                    },
                    exporting: {
                        enabled: false
                    },
                    lang: {
                        decimalPoint: ',',
                        thousandsSep: '.'
                    },
                    legend: {
                        enabled: false,
                        layout: 'vertical',
                        align: 'right',
                        verticalAlign: 'top',
                        x: 10,
                        y: 0,
                        floating: true,
                        width: 170,
                        symbolWidth: 12,
                        itemMarginTop: 5,
                        itemMarginBottom: 5,
                        padding: 12,
                        backgroundColor: 'white',
                        borderWidth: 1,
                        borderColor: '#ccc',
                        itemStyle: {
                            fontWeight: 300
                        },
                        navigation: {
                            style: {
                                fontWeight: 400,
                            }
                        }
                    },
                    plotOptions: {
                        area: {
                            fillOpacity: 0.2,
                            lineWidth: 0.3,
                            marker: {
                                radius: 3,
                                states: {
                                    hover: {
                                        radius: 6,
                                        fillOpacity: 0.4,
                                        fillColor: 'white',
                                        lineWidth: 4,
                                        lineColor: '#5e385d'
                                    }
                                }
                            },
                            states: {
                                hover: {
                                    lineWidth: 0.4
                                }
                            }
                        }
                    },
                    tooltip: {
                        borderWidth: 0,
                        borderRadius: 0,
                        backgroundColor: null,
                        shadow: false,
                        useHTML: true,
                        formatter: function() {
                            var s = '<strong>' + Highcharts.dateFormat('%m/%e/%Y', this.x) + '</strong>' + '<hr>';
                            $.each(this.points, function () {
                                s += this.series.name + ': ' + this.y + '<br>';
                            });
                            return s;
                        },
                        shared: true,
                        crosshairs: {
                            color: 'white',
                            dashStyle: 'solid'
                        }
                    },
                    yAxis: {
                        gridLineColor: 'white',
                        yDecimals: 2,
                        gridLineWidth: 1,
                        title : {
                            text: ''
                        },
                        labels: {
                            style: {
                                color: '#adadad',
                                fontSize: '14px',
                                fontWeight: 400
                            },
                            formatter: function () {
                                // don't print 0 on the y-axis if it's the first label
                                if (this.value === 0 && this.isFirst) {
                                    return null;
                                }
                                return this.value;
                            }
                        }
                    }
                },
                title: {
                    text: ''
                },
                xAxis: {
                    type: 'datetime',
                    lineColor: 'transparent',
                    tickLength: 0,
                    tickInterval: 5 * 24 * 60 * 60 * 1000,
                    title : {
                        text: ''
                    },
                    labels: {
                        y: 24,
                        style: {
                            color: 'white',
                            fontSize: '14px',
                            fontWeight: 400
                        },
                        formatter: function() {
                            return Highcharts.dateFormat('%m/%e/%Y', this.value);
                        }
                    }
                },
                series: [{
                    name: 'Candidates Added',
                    color: '#5e385d',
                    pointStart: getPointStart(vm.chartFilters.daysBack),
                    pointInterval: getPointInterval(vm.chartFilters.daysBack),
                    data: getData(vm.chartFilters.daysBack)
                }],
                func: function (chart) {
                    vm.chart = chart;
                }
            };

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

        function redrawChart() {
            vm.chart.reflow();
            vm.chartConfig.getHighcharts().reflow();
        }

        function updateChart(daysBack) {

            // changing through highcharts-ng config will animate the axis changes
            var series = vm.chartConfig.series[0];
            series.pointStart = getPointStart(daysBack);
            series.pointInterval = getPointInterval(daysBack);
            series.data = getData(daysBack);

            // update() = no animation
            //vm.chart.series[0].update({
            //    pointStart: getPointStart(daysBack),
            //    pointInterval: getPointInterval(daysBack),
            //    data: getData(daysBack)
            //});
        }

        function getPointStart(daysBack) {
            var d = new Date();
            d.setDate(d.getDate() - daysBack - 1 /* don't include today */);
            d.setHours(0);
            d.setMinutes(0);
            d.setSeconds(0);
            return d.getTime();
        }

        function getPointInterval(daysBack) {
            var day = 24 * 60 * 60 * 1000;
            if (daysBack === 1) {
                return day * Math.floor(daysBack / 12) / 24; // @TODO update x-axis labels to hours
            } else if (daysBack === 7) {
                return day * Math.floor(daysBack / 7); // => expects 7 data points
            } else if (daysBack === 30) {
                return day * Math.floor(daysBack / 15);
            } else if (daysBack === 60) {
                return day * Math.floor(daysBack / 15);
            } else if (daysBack === 90) {
                return day * Math.floor(daysBack / 15);
            }
        }

        function getData(daysBack) {
            if (daysBack === 1) {
                return aggregate(dataSetLast24Hours, 24, 12);
            } else if (daysBack === 7) {
                return aggregate(dataSetLast90Days, daysBack, 7);
            } else if (daysBack === 30) {
                return aggregate(dataSetLast90Days, daysBack, 15);
            } else if (daysBack === 60) {
                return aggregate(dataSetLast90Days, daysBack, 15);
            } else if (daysBack === 90) {
                return aggregate(dataSetLast90Days, daysBack, 15);
            }
        }

        function aggregate(data, daysBack, dataPoints) {
            var aggregate = [];
            var newData = data.slice(data.length - daysBack);
            var dataGroupSize = Math.max(Math.floor(daysBack / dataPoints), 1);
            while (newData.length >= dataGroupSize) {
                aggregate.unshift(newData.splice(newData.length - dataGroupSize).reduce(function (prev, curr) {
                    return prev + curr;
                }));
            }
            return aggregate;
        }
    }
})();
