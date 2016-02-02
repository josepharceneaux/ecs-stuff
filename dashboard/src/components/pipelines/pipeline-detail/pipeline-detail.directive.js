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
                    name: 'Total Candidates',
                    tooltip: 'Total Candidates in the pipeline',
                    value: '865',
                    change: '<span class="negative">(-10%)</span>'
                },
                {
                    name: 'New Candidates',
                    tooltip: 'candidates added to that pipeline in the last 30 days',
                    value: '500',
                    change: '2 New Today <span class="negative">(-2%)</span>'
                },
                {
                    name: 'Smart Lists',
                    tooltip: 'Total number of Smart Lists associated with that pipeline',
                    value: '10',
                    change: '<span class="positive">(+10%)</span>'
                },
                {
                    name: 'Total Engagement',
                    tooltip: '% of candidates engaged through all of your pipelines',
                    value: '63%',
                    change: '<span class="positive">(+25%)</span>'
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

            vm.candidateCards = [
                {
                    name: 'Bob Smith',
                    initials: 'BS',
                    photo: '/images/placeholder/candidates/1.jpg',
                    current: 'Senior Software Engineer at Google',
                    activity: 'Bob recently viewed your email'
                },
                {
                    name: 'Kevin Thompson',
                    initials: 'KT',
                    photo: '/images/placeholder/candidates/2.jpg',
                    current: 'Java Engineer at Facebook',
                    activity: 'Kevin responded to your email'
                },
                {
                    name: 'Lenny Seager',
                    initials: 'LS',
                    photo: '/images/placeholder/candidates/3.jpg',
                    current: 'Computer Science Student',
                    activity: 'Lenny responded to your email'
                },
                {
                    name: 'Tom Chansky',
                    initials: 'TC',
                    photo: '/images/placeholder/candidates/4.jpg',
                    current: 'iOS Engineer at AirBnB',
                    activity: 'Tom viewed your email yesterday'
                },
                {
                    name: 'Chris Pratt',
                    initials: 'CP',
                    photo: '/images/placeholder/candidates/5.jpg',
                    current: 'Android Developer - Freelance',
                    activity: 'Chris clicked on your email'
                },
                {
                    name: 'Megi Theodhor',
                    initials: 'MT',
                    photo: '/images/placeholder/candidates/6.jpg',
                    current: 'Frontend Engineer at Uber',
                    activity: 'Megi accepted an event invite'
                },
                {
                    name: 'Julie Thomas',
                    initials: 'JT',
                    photo: '/images/placeholder/candidates/7.jpg',
                    current: 'Senior Software Engineer',
                    activity: 'Julie accepted an event invite'
                },
                {
                    name: 'Rob Overman',
                    initials: 'RO',
                    photo: '/images/placeholder/candidates/8.jpg',
                    current: 'Android App Enthusiast',
                    activity: 'Rob commented on your FB post'
                },
                {
                    name: 'Mike Gueyne',
                    initials: 'MS',
                    photo: '/images/placeholder/candidates/9.jpg',
                    current: 'Software Engineer at Amazon',
                    activity: 'Michelle accepted an event invite'
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
                    avatar: '/images/placeholder/profiles/prof1e.jpg',
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
                    name: 'Rachel Sweezik',
                    team: 'Google Rockstars',
                    avatar: '/images/placeholder/profiles/prof1h.jpg',
                    value: 6
                },
                {
                    name: 'Tim Christianson',
                    team: 'Google SF',
                    avatar: '/images/placeholder/profiles/prof1i.jpg',
                    value: 5
                },
                {
                    name: 'Amy whitter',
                    team: 'Google SF',
                    avatar: '/images/placeholder/profiles/prof1j.jpg',
                    value: 3
                },
                {
                    name: 'Kate Ruthorford',
                    team: 'Google SF',
                    avatar: '/images/placeholder/profiles/prof1k.jpg',
                    value: 2
                }
            ];

            vm.redrawChart = function () {

                vm.chart.reflow();

            };

            vm.chart = new Highcharts.Chart({
                chart: {
                    renderTo: 'growth-chart',
                    type: 'area',
                    backgroundColor: null,
                    spacingLeft: 40,
                    spacingRight: 40,
                    spacingTop: 50,
                    style: {
                        fontFamily: '"Roboto", "Helvetica Neue", Helvetica, Arial, sans-serif',
                        fontWeight: 300
                    },
                    reflow: true
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
                        text: ''
                    },
                    labels: {
                        y: 24,
                        style: {
                            color: '#fff',
                            fontSize: '14px',
                            fontWeight: 400
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
                        text: ''
                    },
                    labels: {
                        style: {
                            color: '#adadad',
                            fontSize: '14px',
                            fontWeight: 400
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
                    enabled: false,
                    layout: 'vertical',
                    align: 'right',
                    verticalAlign: 'top',
                    x: -30,
                    y: -20,
                    followPointer: true,
                    floating: true,
                    width: 170,
                    symbolWidth: 12,
                    itemMarginTop: 5,
                    itemMarginBottom: 5,
                    padding: 12,
                    backgroundColor: '#FFFFFF',
                    borderWidth: 1,
                    borderColor: '#cccccc',
                    itemStyle: {
                        fontWeight: 300
                    },
                    navigation: {
                        style: {
                            fontWeight: 400,
                        }
                    },
                },
                tooltip: {
                    borderWidth: 0,
                    borderRadius: 0,
                    backgroundColor: null,
                    shadow: false,
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
                        animation: {
                            duration: 1000
                        },
                        fillOpacity: 0.2,
                        lineWidth:.3,
                        marker: {
                            enabled: true,
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
                    name: 'Candidates Added',
                    color: '#5e385d',
                    pointStart: Date.UTC(2015, 0, 1),
                    pointInterval: 30 * 24 * 3600 * 1000,
                    data: [0, 20, 50, 80, 120, 60, 150, 110, 112, 92, 20, 40, 80, 100]
                }]
            });

            vm.totalCandidates = {
                graph: {}
            };

        }
    }
})();
