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
    ControllerFunction.$inject = ['logger', '$mdEditDialog', '$q'];

    /* @ngInject */
    function ControllerFunction(logger, $mdEditDialog, $q) {
        var vm = this;

        init();
        activate();

        function activate() {
            logger.log('Activated Pipelines Overview View');
        }

        function init() {

            $('#pipelineDetailsViewChart').highcharts({
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
                title: {
                    text: ''
                },
                lang: {
                    decimalPoint: ',',
                    thousandsSep: '.'
                },
                xAxis: {
                    type: 'datetime',
                    lineColor: 'transparent',
                    tickLength: 0,
                    endOnTick: true,
                    title : {
                        text: ""
                    },
                    labels: {
                        y: 24,
                        style: {
                            color: '#fff',
                            fontSize: '14px',
                            fontWeight: "400"
                        },
                        formatter: function() {
                            return Highcharts.dateFormat('%m/%e/%Y', this.value);
                        }
                    }
                },
                yAxis: {
                    gridLineColor: '#fff',
                    yDecimals: 2,
                    gridLineWidth: 1,
                    title : {
                        text: ""
                    },
                    labels: {
                        style: {
                            color: '#adadad',
                            fontSize: '14px',
                            fontWeight: "400"
                        },
                        formatter: function () {
                            if (this.value != 0) {
                                return this.value;
                            } else {
                                return null;
                            }
                        }
                    }
                },
                exporting: {
                    enabled: false
                },
                credits: {
                    enabled: false
                },
                legend: {
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
                    backgroundColor: '#FFFFFF',
                    borderWidth: 1,
                    borderColor: "#cccccc",
                    itemStyle: {
                      "fontWeight":"300"
                    },
                    navigation: {
                        style: {
                            fontWeight: '400',
                        }
                    }
                },
                tooltip: {
                    borderWidth:0,
                    borderRadius:0,
                    backgroundColor: null,
                    shadow:false,
                    useHTML: true,
                    formatter: function() {
                        var s = '<b>' + Highcharts.dateFormat('%m/%e/%Y', this.x) + '</b>' + '<hr/>';
                        $.each(this.points, function () {
                            s += this.series.name + ': ' + this.y + '<br/>';
                        });
                        return s;
                    },
                    shared: true,
                    crosshairs: {
                        color: 'white',
                        dashStyle: 'solid'
                    }
                },
                plotOptions: {
                    area: {
                        animation: true,
                        fillOpacity: 0.2,
                        lineWidth: 0.2,
                        marker: {
                            enabled: false,
                            symbol: 'circle',
                            radius: 2,
                            states: {
                                hover: {
                                    enabled: true
                                }
                            }
                        },
                        states: {
                            hover: {
                                lineWidth: 0.2
                            }
                        }
                    }
                },
                series: [{
                    name: 'Legend 1',
                    color: '#907f90',
                    pointStart: Date.UTC(2016, 0, 1),
                    pointInterval: 30 * 24 * 3600 * 1000,
                    data: [0, 2000, 800, 6000, 500, 2500, 1500, 2000, 1000, 500]
                }, {
                    name: 'Legend 2',
                    color: '#97b99b',
                    pointStart: Date.UTC(2016, 0, 1),
                    pointInterval: 30 * 24 * 3600 * 1000,
                    data: [0, 1000, 500, 5000, 1500, 800, 1000, 500, 300, 150]
                }, {
                    name: 'Legend 3',
                    color: '#6ba5ae',
                    pointStart: Date.UTC(2016, 0, 1),
                    pointInterval: 30 * 24 * 3600 * 1000,
                    data: [0, 500, 300, 1500, 200, 800, 500, 550, 200, 50]
                }]
            });

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

            vm.callouts = [
                {
                    name: 'Total Pipelines',
                    value: '25'
                },
                {
                    name: 'Total Candidates',
                    value: '10,000'
                },
                {
                    name: 'Unique Candidates',
                    value: '800'
                },
                {
                    name: 'Candidates Today',
                    value: '10'
                }
            ];

            vm.pipelines = [
                {
                    title: 'Java Developer',
                    width: 100,
                    value: '45'
                },
                {
                    title: 'Rails Developer',
                    width: 80,
                    value: '35'
                },
                {
                    title: 'Angular Developer',
                    width: 70,
                    value: '20'
                },
                {
                    title: 'PHP Developer',
                    width: 65,
                    value: '10'
                },
                {
                    title: 'Python Developer',
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
                    limit: 10,
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
                            created: new Date('2015-12-17T03:24:00')
                        }, {
                            id: 2,
                            name: 'Rails Developer',
                            candidates: 870,
                            newCandidates: 12,
                            created: new Date('2015-11-17T03:24:00')
                        }, {
                            id: 3,
                            name: 'PHP Developer',
                            candidates: 134,
                            newCandidates: 22,
                            created: new Date('2015-10-17T03:24:00')
                        }, {
                            id: 4,
                            name: 'California based',
                            candidates: 713,
                            newCandidates: 32,
                            created: new Date('2015-02-17T03:24:00')
                        }, {
                            id: 5,
                            name: 'New York based',
                            candidates: 632,
                            newCandidates: 72,
                            created: new Date('2015-08-17T03:24:00')
                        }, {
                            id: 6,
                            name: 'Python Developer',
                            candidates: 823,
                            newCandidates: 100,
                            created: new Date('2015-09-12T03:24:00')
                        }, {
                            id: 7,
                            name: 'Angular Dev',
                            candidates: 189,
                            newCandidates: 34,
                            created: new Date('2015-03-17T03:24:00')
                        }, {
                            id: 8,
                            name: 'Backbone Dev',
                            candidates: 369,
                            newCandidates: 77,
                            created: new Date('2015-04-17T03:24:00')
                        }, {
                            id: 9,
                            name: 'Europe based',
                            candidates: 932,
                            newCandidates: 123,
                            created: new Date('2015-06-17T03:24:00')
                        }, {
                            id: 10,
                            name: 'Canada based',
                            candidates: 453,
                            newCandidates: 62,
                            created: new Date('2015-04-16T03:24:00')
                        }, {
                            id: 11,
                            name: 'China based',
                            candidates: 824,
                            newCandidates: 103,
                            created: new Date('2015-06-08T03:24:00')
                        }, {
                            id: 12,
                            name: '10 Yr Experienced',
                            candidates: 123,
                            newCandidates: 15,
                            created: new Date('2015-08-17T03:24:00')
                        }, {
                            id: 13,
                            name: 'Senior developer',
                            candidates: 253,
                            newCandidates: 29,
                            created: new Date('2015-03-21T03:24:00')
                        }, {
                            id: 14,
                            name: 'Software Tester',
                            candidates: 521,
                            newCandidates: 64,
                            created: new Date('2015-01-17T03:24:00')
                        }, {
                            id: 15,
                            name: 'Software designer',
                            candidates: 623,
                            newCandidates: 89,
                            created: new Date('2015-05-18T03:24:00')
                        }, {
                            id: 16,
                            name: 'Database Engineer',
                            candidates: 354,
                            newCandidates: 65,
                            created: new Date('2015-05-17T03:24:00')
                        }, {
                            id: 17,
                            name: 'IOS Developer',
                            candidates: 698,
                            newCandidates: 98,
                            created: new Date('2015-09-11T03:24:00')
                        }, {
                            id: 18,
                            name: 'Android Developer',
                            candidates: 693,
                            newCandidates: 20,
                            created: new Date('2015-06-27T03:24:00')
                        }, {
                            id: 19,
                            name: 'Business Admin',
                            candidates: 563,
                            newCandidates: 98,
                            created: new Date('2015-08-27T03:24:00')
                        }, {
                            id: 20,
                            name: 'Trainer',
                            candidates: 951,
                            newCandidates: 156,
                            created: new Date('2015-12-06T03:24:00')
                        }
                    ]
                }
            };

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
