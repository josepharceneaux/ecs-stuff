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
            scope: {
            },
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
        }
    }
})();
