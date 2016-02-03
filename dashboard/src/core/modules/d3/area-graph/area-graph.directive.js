// -------------------------------------
//   Line Graph
//   ->
// -------------------------------------

(function () {
    'use strict';

    angular
        .module('app.core')
        .directive('gtAreaGraph', directiveFunction)
        .controller('AreaGraphController', ControllerFunction)
        .provider('areaGraphConfig', configProviderFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = ['areaGraphConfig'];

    /* @ngInject */
    function directiveFunction(areaGraphConfig) {

        var directive = {
            restrict: 'AE',
            require: ['gtAreaGraph'],
            templateUrl: 'core/modules/d3/area-graph/area-graph.html',
            replace: true,
            scope: {
                config: '=?'
            },
            controller: 'AreaGraphController',
            controllerAs: 'areaGraph',
            link: linkFunction
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = [];

    /* @ngInject */
    function ControllerFunction() {
        var vm = this;

        var dataSetLast90Days;

        vm.redrawChart = redrawChart;
        vm.updateChart = updateChart;

        init();

        function init() {

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
                        title: {
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
                    title: {
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
            if (daysBack === 7) {
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
            if (daysBack === 7) {
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

    function linkFunction(scope, elem, attrs, ctrls) {
        //
    }

    function configProviderFunction() {
        var config;
        this.setOptions = function (options) {
            if (config) {
                throw new Error("Already configured.");
            }
            if (!(options instanceof Object)) {
                throw new TypeError("Invalid argument: `config` must be an `Object`.");
            }
            config = angular.extend({}, options);
            return config;
        };
        this.$get = function () {
            var Config = function () {
                function Config() {}

                Object.defineProperties(Config.prototype, {
                    getOptions: {
                        value: function getOptions() {
                            return angular.copy(config);
                        },
                        writable: true,
                        enumerable: true,
                        configurable: true
                    },
                });
                return Config;
            }();
            return new Config();
        };
        this.$get.$inject = [];
    }
})();
