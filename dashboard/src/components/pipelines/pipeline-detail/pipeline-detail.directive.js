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
        vm.pipelineId = 1337;

        init();
        activate();

        function activate() {
            logger.log('Activated Pipeline Detail View');
        }

        function init() {

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

            vm.contributors = [
                {
                    name: 'Haohong Xu',
                    avatar: '//placehold.it/80x80',
                    value: 20
                },
                {
                    name: 'Osman Masood',
                    avatar: '//placehold.it/80x80',
                    value: 18
                },
                {
                    name: 'Jason Provencher',
                    avatar: '//placehold.it/80x80',
                    value: 15
                },
                {
                    name: 'Haohong Xu',
                    avatar: '//placehold.it/80x80',
                    value: 12
                },
                {
                    name: 'Haohong Xu',
                    avatar: '//placehold.it/80x80',
                    value: 10
                }
            ];

            pipelinesDetailService.getPipelineDetail(vm.pipelineId).then(function (response) {
                vm.pipelineDetails = response;
                pipelinesDetailService.getPipelineCandidateInfo(vm.pipelineDetails.search_params).then(function (response) {
                    vm.candidateInfo = response;
                });
            });

            pipelinesDetailService.getPipelineCandidatesCount(vm.pipelineId).then(function (response) {
                vm.candidatesCount = response;
            });

            pipelinesDetailService.getPipelineSmartlistsCount(vm.pipelineId).then(function (response) {
                vm.smartLists = response;
            });

        }
    }
})();
