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
                onFilterChange: '&graphOnFilterChange',
                colorOptions: '=?graphColorOptions'
            },
            controller: 'AreaGraphController',
            controllerAs: 'areaGraph',
            bindToController: true,
            link: linkFunction
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['areaGraphConfig'];

    /* @ngInject */
    function ControllerFunction(areaGraphConfig) {
        var vm = this;

        vm.redrawChart = redrawChart;

        init();

        function init() {
            if (!angular.isObject(vm.config)) {
                throw new TypeError("Invalid argument: `vm.config` must be an `Object`.");
            }
            mergeConfigs(vm.config, getDefaultConfig(vm.colorOptions));
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
            var colorOptions = areaGraphConfig.getOptions().colors;
            if (vm.colorOptions) {
                if (!angular.isObject(vm.colorOptions)) {
                    throw new TypeError("Invalid argument: `vm.colorOptions` must be an `Object`.");
                }
                angular.merge(colorOptions, vm.colorOptions);
            }
            return {
                options: {
                    chart: {
                        type: 'area',
                        backgroundColor: colorOptions.chart.backgroundColor,
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
                        backgroundColor: colorOptions.legend.backgroundColor,
                        borderWidth: 1,
                        borderColor: colorOptions.legend.borderColor,
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
                                fillColor: colorOptions.plotOptions.marker.fillColor,
                                lineColor: colorOptions.plotOptions.marker.lineColor,
                                states: {
                                    hover: {
                                        radius: 6,
                                        fillOpacity: 0.4,
                                        fillColor: colorOptions.plotOptions.marker.states.hover.fillColor,
                                        lineWidth: 4,
                                        lineColor: colorOptions.plotOptions.marker.states.hover.lineColor
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
                            color: colorOptions.tooltip.crosshairsColor,
                            dashStyle: 'solid'
                        }
                    },
                    yAxis: {
                        gridLineColor: colorOptions.yAxis.gridLineColor,
                        yDecimals: 2,
                        gridLineWidth: 1,
                        title: {
                            text: ''
                        },
                        labels: {
                            style: {
                                color: colorOptions.yAxis.labelColor,
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
                    lineColor: colorOptions.xAxis.lineColor,
                    tickLength: 0,
                    title: {
                        text: ''
                    },
                    labels: {
                        y: 24,
                        style: {
                            color: colorOptions.xAxis.labelColor,
                            fontSize: '14px',
                            fontWeight: 400
                        },
                        formatter: function () {
                            return Highcharts.dateFormat('%m/%e/%Y', this.value);
                        }
                    }
                },
                series: [{
                    color: colorOptions.series.color
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
        var defaultConfig = {
            colors: {
                chart: {
                    backgroundColor: null
                },
                legend: {
                    backgroundColor: 'white',
                    borderColor: '#ccc'
                },
                plotOptions: {
                    marker: {
                        fillColor: undefined,
                        lineColor: undefined,
                        states: {
                            hover: {
                                fillColor: 'white',
                                lineColor: '#5e385d'
                            }
                        }
                    }
                },
                tooltip: {
                    crosshairsColor: 'white'
                },
                yAxis: {
                    gridLineColor: 'white',
                    labelColor: '#adadad'
                },
                xAxis: {
                    lineColor: 'transparent',
                    labelColor: 'white'
                },
                series: {
                    color: '#5e385d'
                }
            }
        };
        var config = angular.copy(defaultConfig);
        this.setOptions = function (options) {
            if (!angular.isObject(options)) {
                throw new TypeError("Invalid argument: `config` must be an `Object`.");
            }
            if (!angular.isObject(options.colors)) {
                throw new TypeError("Invalid argument: `config.colors` must be an `Object`.");
            }
            angular.merge(config, options);
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
