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

        }
    }
})();
