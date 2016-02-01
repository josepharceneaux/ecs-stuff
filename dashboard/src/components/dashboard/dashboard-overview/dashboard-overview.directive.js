(function () {
    'use strict';

    angular.module('app.dashboard')
        .directive('gtDashboardOverview', directiveFunction)
        .controller('DashboardOverviewController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/dashboard/dashboard-overview/dashboard-overview.html',
            replace: true,
            scope: {},
            controller: 'DashboardOverviewController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['logger', '$mdDialog', '$mdMedia'];

    /* @ngInject */
    function ControllerFunction(logger, $mdDialog, $mdMedia) {
        var vm = this;

        init();
        activate();
        showWelcomeDialog();

        function init() {
            // example for md-dialog example
            vm.items = [1, 2, 3];

            vm.itemsPerPageOptions = [
                { value: 5, name: '5 per page' },
                { value: 10, name: '10 per page' },
                { value: 15, name: '15 per page' }
            ];
            vm.pipelinesPerPage = vm.itemsPerPageOptions[0].value;
            vm.campaignsPerPage = vm.itemsPerPageOptions[0].value;

            vm.heroCharts = [
                { id: 'totalEngagement', name: 'Total Engagement' }
            ];

            vm.heroChartDateRanges = [
                { id: '15d', name: '15d' },
                { id: '30d', name: '30d' },
                { id: '60d', name: '60d' }
            ];
            vm.heroChartDateRange = vm.heroChartDateRanges[0];

            vm.totalCandidates = {};
            vm.totalCandidates.graph = {};
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

            vm.topContributionsDateRanges = [
                { id: '7-days', name: '7d' },
                { id: '30-days', name: '30d' },
                { id: '60-days', name: '60d' },
                { id: '182-days', name: '6mo' },
                { id: '365-days', name: '1yr' }
            ];
            vm.selectedTopContributionsDateRange = vm.topContributionsDateRanges[0];


            vm.pipelineEngagement = {};
            vm.pipelineEngagement.graph = {};
            vm.pipelineEngagement.graph.data = 33;

            vm.talentPipelinesViewOptions = [
                { id: 'candidate-count-by-pipelines', name: 'Candidate Count by Pipelines' },
                { id: 'candidate-growth-by-pipelines', name: 'Candidate Growth by Pipelines' },
                { id: 'candidate-growth-by-user', name: 'Candidate Growth by User' },
                { id: 'candidate-opt-outs-by-pipelines', name: 'Candidate Opt-Outs by Pipelines' },
                { id: 'engagement-by-pipelines', name: 'Engagement by Pipelines' }
            ];

            vm.activeEngagementViewOptions = [
                { id: 'candidate-count-by-pipelines', name: 'Candidate Count by Pipelines' },
                { id: 'candidate-growth-by-pipelines', name: 'Candidate Growth by Pipelines' },
                { id: 'candidate-growth-by-user', name: 'Candidate Growth by User' },
                { id: 'candidate-opt-outs-by-pipelines', name: 'Candidate Opt-Outs by Pipelines' },
                { id: 'engagement-by-pipelines', name: 'Engagement by Pipelines' }
            ];

            vm.talentPipelines = [
                {
                    id: '0cc175b9c0f1b6a831c399e269772661',
                    name: 'Sr. Java Developers in CA',
                    totalCandidates: 608,
                    dateCreated: '2015-03-02',
                    growth: '+67',
                    engagement: '20%'
                },
                {
                    id: '187ef4436122d1cc2f40dc2b92f0eba0',
                    name: 'Lead Ninja Trainer',
                    totalCandidates: '23',
                    dateCreated: '2015-06-06',
                    growth: '+12',
                    engagement: '50%'
                },
                {
                    id: '900150983cd24fb0d6963f7d28e17f72',
                    name: 'Adobe Acrobat Updater',
                    totalCandidates: '502',
                    dateCreated: '2015-06-21',
                    growth: '+200',
                    engagement: '220%'
                },
                {
                    id: 'e2fc714c4727ee9395f324cd2e7f331f',
                    name: 'First Class Joomla Hacker',
                    totalCandidates: '230',
                    dateCreated: '2015-04-25',
                    growth: '+567',
                    engagement: '231%'
                },
                {
                    id: 'ab56b4d92b40713acc5af89985d4b786',
                    name: 'Dreamweaver RockStar',
                    totalCandidates: '608',
                    dateCreated: '2015-03-22',
                    growth: '+67',
                    engagement: '210%'
                },
                {
                    id: '94af155370ff640425a75c743ade5787',
                    name: 'Lazy Exotic Environment Technologist',
                    totalCandidates: '20',
                    dateCreated: '2015-02-15',
                    growth: '+45',
                    engagement: '210%'
                },
                {
                    id: 'a98337be62e583dcf2d5c12af8689b5f',
                    name: 'Master CSS-layout Spec Designer',
                    totalCandidates: '25',
                    dateCreated: '2015-04-15',
                    growth: '+67',
                    engagement: '210%'
                },
                {
                    id: '6c0b23ddc797500cc16b8a42a5a49105',
                    name: 'Fax Machine Masterer',
                    totalCandidates: '132',
                    dateCreated: '2015-10-22',
                    growth: '+33',
                    engagement: '210%'
                },
                {
                    id: 'f476c08a6c8df70a93da1b5b5b984749',
                    name: 'Digital Prophet',
                    totalCandidates: '14',
                    dateCreated: '2015-02-29',
                    growth: '+67',
                    engagement: '210%'
                },
                {
                    id: '675cfd6254c8cfd772528ba68ebe094c',
                    name: 'Evolutionary Thinker of Free Code',
                    totalCandidates: '372',
                    dateCreated: '2015-06-29',
                    growth: '+17',
                    engagement: '160%'
                },
                {
                    id: 'fc385b2ce9e18355a66d5da17fae0c85',
                    name: 'Guru Master Business Hero',
                    totalCandidates: '462',
                    dateCreated: '2015-09-21',
                    growth: '+163',
                    engagement: '120%'
                },
                {
                    id: '6f306543270ec470ca77c211635e6a68',
                    name: 'Professional Pizza Reheater',
                    totalCandidates: '156',
                    dateCreated: '2015-08-12',
                    growth: '+67',
                    engagement: '210%'
                },
                {
                    id: 'bec568d412ac0d47c8376f01412256a7',
                    name: 'Junior Beard Developer',
                    totalCandidates: '158',
                    dateCreated: '2015-01-28',
                    growth: '+37',
                    engagement: '21%'
                },
                {
                    id: 'ec8d110326e67dcd8a02cb2649e5ea41',
                    name: 'Powerful Newsletter Unsubscriber',
                    totalCandidates: '68',
                    dateCreated: '2015-06-12',
                    growth: '+167',
                    engagement: '10%'
                },
                {
                    id: '31c399e2697726610cc175b9c0f1b6a8',
                    name: 'Sr. Java Developers in CA',
                    totalCandidates: 608,
                    dateCreated: '2015-03-02',
                    growth: '+67',
                    engagement: '20%'
                },
                {
                    id: '2f40dc2b92f0eba0187ef4436122d1cc',
                    name: 'Lead Ninja Trainer',
                    totalCandidates: '23',
                    dateCreated: '2015-06-06',
                    growth: '+12',
                    engagement: '50%'
                },
                {
                    id: 'd6963f7d28e17f72900150983cd24fb0',
                    name: 'Adobe Acrobat Updater',
                    totalCandidates: '502',
                    dateCreated: '2015-06-21',
                    growth: '+200',
                    engagement: '220%'
                },
                {
                    id: '95f324cd2e7f331fe2fc714c4727ee93',
                    name: 'First Class Joomla Hacker',
                    totalCandidates: '230',
                    dateCreated: '2015-04-25',
                    growth: '+567',
                    engagement: '231%'
                },
                {
                    id: 'cc5af89985d4b786ab56b4d92b40713a',
                    name: 'Dreamweaver RockStar',
                    totalCandidates: '608',
                    dateCreated: '2015-03-22',
                    growth: '+67',
                    engagement: '210%'
                },
                {
                    id: '25a75c743ade578794af155370ff6404',
                    name: 'Lazy Exotic Environment Technologist',
                    totalCandidates: '20',
                    dateCreated: '2015-02-15',
                    growth: '+45',
                    engagement: '210%'
                },
                {
                    id: 'f2d5c12af8689b5fa98337be62e583dc',
                    name: 'Master CSS-layout Spec Designer',
                    totalCandidates: '25',
                    dateCreated: '2015-04-15',
                    growth: '+67',
                    engagement: '210%'
                },
                {
                    id: 'c16b8a42a5a491056c0b23ddc797500c',
                    name: 'Fax Machine Masterer',
                    totalCandidates: '132',
                    dateCreated: '2015-10-22',
                    growth: '+33',
                    engagement: '210%'
                },
                {
                    id: '93da1b5b5b984749f476c08a6c8df70a',
                    name: 'Digital Prophet',
                    totalCandidates: '14',
                    dateCreated: '2015-02-29',
                    growth: '+67',
                    engagement: '210%'
                },
                {
                    id: '72528ba68ebe094c675cfd6254c8cfd7',
                    name: 'Evolutionary Thinker of Free Code',
                    totalCandidates: '372',
                    dateCreated: '2015-06-29',
                    growth: '+17',
                    engagement: '160%'
                },
                {
                    id: 'a66d5da17fae0c85fc385b2ce9e18355',
                    name: 'Guru Master Business Hero',
                    totalCandidates: '462',
                    dateCreated: '2015-09-21',
                    growth: '+163',
                    engagement: '120%'
                },
                {
                    id: 'ca77c211635e6a686f306543270ec470',
                    name: 'Professional Pizza Reheater',
                    totalCandidates: '156',
                    dateCreated: '2015-08-12',
                    growth: '+67',
                    engagement: '210%'
                },
                {
                    id: 'c8376f01412256a7bec568d412ac0d47',
                    name: 'Junior Beard Developer',
                    totalCandidates: '158',
                    dateCreated: '2015-01-28',
                    growth: '+37',
                    engagement: '21%'
                },
                {
                    id: '8a02cb2649e5ea41ec8d110326e67dcd',
                    name: 'Powerful Newsletter Unsubscriber',
                    totalCandidates: '68',
                    dateCreated: '2015-06-12',
                    growth: '+167',
                    engagement: '10%'
                }
            ];

            vm.campaigns = [
                {
                    id: '8a02cb2649e5ea41ec8d110326e67dcd',
                    date: '2015-09-22',
                    name: 'Python developer blast',
                    engagement: '67%',
                    user: 'Jane Quon',
                    type: 'Email',
                    pipeline: 'Python developer'
                },
                {
                    id: 'c8376f01412256a7bec568d412ac0d47',
                    date: '2015-10-11',
                    name: 'Site Engineers meetup',
                    engagement: '23%',
                    user: 'Wally Gibson',
                    type: 'Event',
                    pipeline: 'Site Reliability Engineers'
                },
                {
                    id: 'ca77c211635e6a686f306543270ec470',
                    date: '2015-08-03',
                    name: 'iOS Developer reachout',
                    engagement: '19%',
                    user: 'Tula Martin',
                    type: 'SMS',
                    pipeline: 'iOS Sr. Developer'
                },
                {
                    id: 'a66d5da17fae0c85fc385b2ce9e18355',
                    date: '2015-07-27',
                    name: 'Finance Opportunities',
                    engagement: '72%',
                    user: 'Lee River',
                    type: 'Email',
                    pipeline: 'Finance Analyst'
                },
                {
                    id: '93da1b5b5b984749f476c08a6c8df70a',
                    date: '2015-05-15',
                    name: 'QA Engineers & Automation',
                    engagement: '56%',
                    user: 'Iris Denney',
                    type: 'Social',
                    pipeline: 'Sr. QA Engineer'
                },
                {
                    id: 'e708864855f3bb69c4d9a213b9108b9f',
                    date: '2015-03-02',
                    name: 'Daily Job Alert',
                    engagement: '67%',
                    user: 'Alan Turing',
                    type: 'Email',
                    pipeline: 'Sr. Java Developers in CA'
                }
            ];

            vm.pipelines = [
                {
                    id: 'e708864855f3bb69c4d9a213b9108b9f',
                    name: 'Senior Java Developers in CA',
                    progress: 1
                },
                {
                    id: '912ec803b2ce49e4a541068d495ab570',
                    name: 'Veterans Hiring Initiative',
                    progress: .78
                },
                {
                    id: 'db83bc9caeaa8443b2bcf02d4b55ebee',
                    name: 'Oracle DBAs Overseas',
                    progress: .25
                },
                {
                    id: '22ca8686bfa31a2ae5f55a7f60009e14',
                    name: 'Oracle DBAs Overseas',
                    progress: .5
                }
            ];

            vm.topSkills = [
                { name: 'Automatic Data Processing' },
                { name: 'Angular JS' },
                { name: 'Hadoop' },
                { name: 'HTML5' },
                { name: 'Apache Jackrabbit' },
                { name: 'Linux' },
                { name: 'Production Management' },
                { name: 'Software Troubleshooting' },
                { name: 'Sybase Unwired Platform' },
                { name: 'Location-Based Services' },
                { name: 'DevOps' },
                { name: 'LTX Credence' }
            ];

            vm.topLocations = [
                { formattedLocation: 'Portland, OR' },
                { formattedLocation: 'Detroit, MI' },
                { formattedLocation: 'Orlando, FL' },
                { formattedLocation: 'Santa Cruz, CA' },
                { formattedLocation: 'Miami, FL' },
                { formattedLocation: 'Seattle, WA' },
                { formattedLocation: 'Olympia, WA' },
                { formattedLocation: 'Dallas, TX' },
                { formattedLocation: 'Denver, CO' }
            ];

            vm.topSites = [
                { location: 'Seattle, WA' },
                { location: 'Olympia, WA' },
                { location: 'Dallas, TX' },
                { location: 'Portland, OR' },
                { location: 'Detroit, MI' },
                { location: 'Orlando, FL' },
                { location: 'Santa Cruz, CA' },
                { location: 'Miami, FL' },
                { location: 'Denver, CO' }
            ];

            vm.topReferrals = [
                { location: 'Miami, FL' },
                { location: 'Seattle, WA' },
                { location: 'Olympia, WA' },
                { location: 'Dallas, TX' },
                { location: 'Denver, CO' },
                { location: 'Portland, OR' },
                { location: 'Detroit, MI' },
                { location: 'Orlando, FL' },
                { location: 'Santa Cruz, CA' }
            ];

            vm.recommendedCandidates = [
                {
                    name: 'Bob Smith',
                    avatar: '/images/placeholder/profiles/prof1a.jpg',
                    current: 'Senior Software Engineer at GetTalent',
                    activity: 'Bob recently viewed your email'
                },
                {
                    name: 'Kevin Thompson',
                    avatar: '/images/placeholder/profiles/prof1b.jpg',
                    current: 'Senior Software Engineer at GetTalent',
                    activity: 'Bob recently viewed your email'
                },
                {
                    name: 'Lenny Seager',
                    avatar: '/images/placeholder/profiles/prof1c.jpg',
                    current: 'Senior Software Engineer at GetTalent',
                    activity: 'Bob recently viewed your email'
                },
                {
                    name: 'Tom Chansky',
                    avatar: '/images/placeholder/profiles/prof1d.jpg',
                    current: 'Senior Software Engineer at GetTalent',
                    activity: 'Bob recently viewed your email'
                },
                {
                    name: 'Chris Pratt',
                    avatar: '/images/placeholder/profiles/prof1h.jpg',
                    current: 'Senior Software Engineer at GetTalent',
                    activity: 'Bob recently viewed your email'
                },
                {
                    name: 'Megi Theodhor',
                    avatar: '/images/placeholder/profiles/prof1f.jpg',
                    current: 'Senior Software Engineer at GetTalent',
                    activity: 'Bob recently viewed your email'
                }
            ];

            vm.topContributors = [
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
                }
            ];

            vm.newCandidateToday = 400;
            vm.teamContributions = 400;

            vm.viewCandidate = function (candidate) {
                
                // TODO: go to candidate detail page
                alert('View candidate: ' + candidate.name);
            
            };

            vm.emailToCandidate = function (candidate) {

                // TODO: email to candidate
                alert('Email to ' + candidate.name);

            };
        }

        function activate() {
            logger.log('Activated Dashboard Overview View');
        }

        function showWelcomeDialog($event) {
            var useFullScreen = ($mdMedia('sm') || $mdMedia('xs'));
            $mdDialog.show({
                controller: DialogController,
                controllerAs: 'vm',
                templateUrl: 'components/onboard/onboard-welcome/onboard-welcome.html',
                parent: angular.element(document.body),
                targetEvent: $event,
                clickOutsideToClose: true,
                fullscreen: useFullScreen
            })
            .then(function (answer) {
                //$scope.status = 'You said the information was "' + answer + '".';
            }, function() {
                //$scope.status = 'You canceled the dialog.';
            });
        };

        DialogController.$inject = ['$scope', '$mdDialog'];

        /* @ngInject */
        function DialogController($scope, $mdDialog) {
            $scope.hide = function() {
                $mdDialog.hide();
            };
            $scope.cancel = function() {
                $mdDialog.cancel();
            };
            $scope.answer = function(answer) {
                $mdDialog.hide(answer);
            };
        }
    }
})();
