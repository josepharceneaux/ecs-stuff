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
            vm.metrics = [
                {
                    name: 'Total Candidates',
                    value: '1000'
                },
                {
                    name: 'Active Campaigns',
                    value: '20'
                },
                {
                    name: 'Smart Lists',
                    value: '10'
                },
                {
                    name: 'Created Date',
                    value: '4/3/16'
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
                },
            ];
        }
    }
})();
