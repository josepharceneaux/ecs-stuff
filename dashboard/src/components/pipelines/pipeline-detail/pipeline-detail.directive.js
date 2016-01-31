(function () {
    'use strict';

    angular.module('app.pipelines')
        .directive('gtPipelineDetail', directiveFunction)
        .controller('PipelineDetailController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/pipelines/pipeline-detail/pipeline-detail.html',
            replace: true,
            scope: {},
            controller: 'PipelineDetailController',
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
            logger.log('Activated Pipeline Detail View');
        }

        function init() {
            vm.callouts = [
                {
                    name: 'Candidates Added',
                    tooltip: 'Fix',
                    value: '500',
                    change: '2 New Today <span class="negative">(-2%)</span>'
                },
                {
                    name: 'Total Candidates',
                    tooltip: 'Fix',
                    value: '865',
                    change: '<span class="negative">(-10%)</span>'
                },
                {
                    name: 'Recommended Candidates',
                    tooltip: 'Fix',
                    value: '10',
                    change: '<span class="positive">(+10%)</span>'
                },
                {
                    name: 'Campaigns',
                    tooltip: 'Fix',
                    value: '10'
                }
            ];

            vm.feeds = [
                {
                    time: '36 minutes ago',
                    text: 'Haohong opened the email from Java Developer campaign'
                },
                {
                    time: '1 hr ago',
                    text: 'Haohong added 54 Candidates'
                },
                {
                    time: '2 hrs ago',
                    text: 'Haohong opened the email from Java Developer campaign'
                },
                {
                    time: '4 hrs ago',
                    text: 'Haohong added 54 Candidates'
                },
                {
                    time: '5 hrs ago',
                    text: 'Haohong opened the email from Java Developer campaign'
                },
                {
                    time: 'Yesterday',
                    text: 'Haohong added 54 Candidates'
                }
            ];

            vm.topSkills = [
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

            vm.candidateCards = [
                {
                    name: 'Bob Smith',
                    initials: 'BS',
                    current: 'Senior Software Engineer at GetTalent',
                    activity: 'Bob recently viewed your email'
                },
                {
                    name: 'Kevin Thompson',
                    initials: 'KT',
                    current: 'Senior Software Engineer at GetTalent',
                    activity: 'Bob recently viewed your email'
                },
                {
                    name: 'Lenny Seager',
                    initials: 'LS',
                    current: 'Senior Software Engineer at GetTalent',
                    activity: 'Bob recently viewed your email'
                },
                {
                    name: 'Tom Chansky',
                    initials: 'TC',
                    current: 'Senior Software Engineer at GetTalent',
                    activity: 'Bob recently viewed your email'
                },
                {
                    name: 'Chris Pratt',
                    initials: 'CP',
                    current: 'Senior Software Engineer at GetTalent',
                    activity: 'Bob recently viewed your email'
                },
                {
                    name: 'Megi Theodhor',
                    initials: 'MT',
                    current: 'Senior Software Engineer at GetTalent',
                    activity: 'Bob recently viewed your email'
                }
            ];

            vm.contributors = [
                {
                    name: 'Bob Smith',
                    team: 'Google Boston',
                    avatar: '/images/placeholder/profiles/prof1a.jpg',
                    value: 60
                },
                {
                    name: 'Katie Fries',
                    team: 'Google SF',
                    avatar: '/images/placeholder/profiles/prof1b.jpg',
                    value: 55
                },
                {
                    name: 'Rachel Thompson',
                    team: 'Google SF',
                    avatar: '/images/placeholder/profiles/prof1c.jpg',
                    value: 45
                },
                {
                    name: 'Chris Chang',
                    team: 'Google SF',
                    avatar: '/images/placeholder/profiles/prof1d.jpg',
                    value: 40
                },
                {
                    name: 'Chrissy Donnelly',
                    team: 'Google Boston',
                    avatar: '/images/placeholder/profiles/prof1h.jpg',
                    value: 10
                },
                {
                    name: 'Sean Zinsmeister',
                    team: 'Google Southwest',
                    avatar: '/images/placeholder/profiles/prof1f.jpg',
                    value: 12
                },
                {
                    name: 'Lauren Freeman',
                    team: 'Google HR',
                    avatar: '/images/placeholder/profiles/prof1g.jpg',
                    value: 10
                },
                {
                    name: 'Chrissy Donnelly',
                    team: 'Google Rockstars',
                    avatar: '/images/placeholder/profiles/prof1h.jpg',
                    value: 10
                },
                {
                    name: 'Sean Zinsmeister',
                    team: 'Google SF',
                    avatar: '/images/placeholder/profiles/prof1f.jpg',
                    value: 12
                },
                {
                    name: 'Lauren Freeman',
                    team: 'Google SF',
                    avatar: '/images/placeholder/profiles/prof1g.jpg',
                    value: 10
                }
            ];

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
                            fontSize: '12px',
                            fontWeight: "bold"
                        },
                        formatter: function() {
                            return Highcharts.dateFormat('%m/%e/%Y', this.value);
                        }
                    }
                },
                yAxis: {
                    gridLineColor: '#fff',
                    yDecimals: 2,
                    gridLineWidth: 1.5,
                    title : {
                        text: ""
                    },
                    labels: {
                        style: {
                            color: '#adadad',
                            fontSize: '12px',
                            fontWeight: "bold"
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
                    x: -30,
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
        }
    }
})();
