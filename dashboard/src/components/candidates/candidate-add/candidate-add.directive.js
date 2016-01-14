(function () {
    'use strict';

    angular.module('app.candidates')
        .directive('gtCandidateAdd', directiveFunction)
        .controller('CandidateAddController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/candidates/candidate-add/candidate-add.html',
            replace: true,
            scope: {
            },
            controller: 'CandidateAddController',
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
            logger.log('Activated Candidate Add View');
        }

        function init() {
            //
        }
    }
})();
