(function () {
    'use strict';

    angular.module('app.candidates')
        .directive('gtCandidateVerify', directiveFunction)
        .controller('CandidateVerifyController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/candidates/candidate-verify/candidate-verify.html',
            replace: true,
            scope: {},
            controller: 'CandidateVerifyController',
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
            logger.log('Activated Candidate Verify View');
        }

        function init() {
            //
        }
    }
})();
