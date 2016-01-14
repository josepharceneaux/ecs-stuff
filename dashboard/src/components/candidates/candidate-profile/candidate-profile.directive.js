(function () {
    'use strict';

    angular.module('app.candidates')
        .directive('gtCandidateProfile', directiveFunction)
        .controller('CandidateProfileController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/candidates/candidate-profile/candidate-profile.html',
            replace: true,
            scope: {},
            controller: 'CandidateProfileController',
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
            logger.log('Activated Candidate Profile View');
        }

        function init() {
            vm.pipelineEngagement = {};
            vm.pipelineEngagement.graph = {};
            vm.pipelineEngagement.graph.data = 33;

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
                    id: '22ca8686bfa31a2ae5f55a7f60009e14',
                    name: 'Oracle DBAs Overseas',
                    progress: .5
                },
                {
                    id: 'db83bc9caeaa8443b2bcf02d4b55ebee',
                    name: 'Oracle DBAs Overseas',
                    progress: .25
                }
            ];
        }
    }
})();
