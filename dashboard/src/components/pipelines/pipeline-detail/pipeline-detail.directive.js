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
    ControllerFunction.$inject = ['$q', 'logger', 'pipelinesDetailService'];

    /* @ngInject */
    function ControllerFunction($q, logger, pipelinesDetailService) {
        var vm = this;
        //How is the pipeline Id going to be set normally? Grabbing from the router $stateParams?
        vm.pipelineId = 1337;

        init();
        activate();

        vm.redrawChart = redrawChart;
        vm.updateChart = updateChart;
        vm.removeFilter = removeFilter;
        var dataSetLast24Hours;
        var dataSetLast90Days;

        function activate() {
            logger.log('Activated Pipeline Detail View');
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
                62, 100, 39, 77, 48, 108, 124, 93, 17, 10,
                5, 52, 54, 19, 41, 12, 29, 59, 29, 106,
                54, 25, 26, 13, 32, 51, 41, 82, 20, 10,
                10, 30, 40, 20, 35, 30, 55, 80, 100, (400-300)];

            vm.chartFilters = {};
            vm.daysFilterOptions = [7, 30, 60, 90];
            vm.chartFilters.daysBack = vm.daysFilterOptions[1];

            vm.chartOptions = {
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
                    tickInterval: 5 * 24 * 60 * 60 * 1000,
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
                    borderColor: '#cccccc',
                    itemStyle: {
                        fontWeight: 300
                    },
                    navigation: {
                        style: {
                            fontWeight: 400,
                        }
                    },
                    enabled: false
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
                        animation: true,
                        fillOpacity: 0.2,
                        lineWidth:.3,
                        marker: {
                            enabled: true,
                            symbol: 'circle',
                            radius: 3,
                            states: {
                                hover: {
                                    radius: 6,
                                    fillOpacity:.4,
                                    fillColor: '#FFFFFF',
                                    lineWidth: 4,
                                    lineColor: '#5e385d'
                                }
                            }
                        },
                        states: {
                            hover: {
                                lineWidth:.4
                            }
                        }
                    }
                },
                series: [{
                    name: 'Candidates Added',
                    color: '#5e385d',
                    pointStart: getPointStart(vm.chartFilters.daysBack),
                    pointInterval: getPointInterval(vm.chartFilters.daysBack),
                    data: getData(vm.chartFilters.daysBack)
                }]
            };

            vm.chart = new Highcharts.Chart(vm.chartOptions);
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
                    value: '200',
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

            pipelinesDetailService.getPipelineDetail(vm.pipelineId).then(function (response) {
                vm.pipelineDetails = response;
                pipelinesDetailService.getPipelineCandidateInfo(vm.pipelineDetails.search_params).then(function (response) {
                    vm.candidateInfo = response;
                    vm.topSkills = processTopSkills(vm.candidateInfo.facets.skills.slice(0, 5));
                    vm.contributors = processContributors(vm.candidateInfo.facets.username.slice(0, 5));
                });
            });

            pipelinesDetailService.getPipelineCandidatesCount(vm.pipelineId).then(function (response) {
                vm.candidatesCount = response;
            });

            pipelinesDetailService.getPipelineSmartlistsCount(vm.pipelineId).then(function (response) {
                vm.smartLists = response;
            });

            function processTopSkills(skillsList) {
                var i;
                var processedSkills = [];
                for (i = 0; i < skillsList.length; i++) {
                    processedSkills.push({
                        title: skillsList[i].value,
                        value: skillsList[i].count,
                        //Is the width in relation to the top skills or the entire pool?
                        width: Math.floor(Math.random() * 50) + 40
                    });
                }
                return processedSkills;
            }

            function processContributors(contributorsList) {
                var i;
                var processedContributors = [];
                for (i = 0; i < contributorsList.length; i++) {
                    processedContributors.push({
                        //value is name attr but test data is empty string or space char
                        name: 'User ' + contributorsList[i].id,
                        avatar: '//placehold.it/80x80',
                        value: contributorsList[i].count
                    })
                }
                return processedContributors;
            }

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
        }

        function updateChart(daysBack) {
            vm.chart.series[0].update({
                pointStart: getPointStart(daysBack),
                pointInterval: getPointInterval(daysBack),
                data: getData(daysBack)
            });
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
