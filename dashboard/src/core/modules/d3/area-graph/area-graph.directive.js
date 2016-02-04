// -------------------------------------
//   Area Graph
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
                config: '=graphConfig',
                title: '=graphTitle',
                filterOptions: '=graphFilterOptions',
                filterValue: '=graphFilterValue',
                onFilterChange: '&graphOnFilterChange'
            },
            controller: 'AreaGraphController',
            controllerAs: 'areaGraph',
            bindToController: true,
            link: linkFunction
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = [];

    /* @ngInject */
    function ControllerFunction() {
        var vm = this;

        vm.redrawChart = redrawChart;

        init();

        function init() {
            if (!(vm.config instanceof Object)) {
                throw new TypeError("Invalid argument: `config` must be an `Object`.");
            }
            mergeConfigs(vm.config, getDefaultConfig);
        }

        function redrawChart() {
            vm.chart.reflow();
        }

        function mergeConfigs() {
            var defaults = getDefaultConfig();
            var originalCallback = vm.config.func;
            vm.config.func = getChartCreatedCallback(originalCallback);
            vm.config = angular.merge(defaults, vm.config);
        }

        function getDefaultConfig() {
            return {
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
                        formatter: function () {
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
                        formatter: function () {
                            return Highcharts.dateFormat('%m/%e/%Y', this.value);
                        }
                    }
                },
                series: [{
                    color: '#5e385d'
                }]
            };
        }

        function getChartCreatedCallback(fn) {
            return function (chart) {
                vm.chart = chart;
                if (typeof fn === 'function') {
                    fn.call(this, chart);
                }
            };
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
