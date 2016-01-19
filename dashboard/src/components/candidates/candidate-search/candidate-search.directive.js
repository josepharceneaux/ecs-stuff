(function () {
    'use strict';

    angular.module('app.candidates')
        .directive('gtCandidateSearch', directiveFunction)
        .controller('CandidateSearchController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/candidates/candidate-search/candidate-search.html',
            replace: true,
            scope: {},
            controller: 'CandidateSearchController',
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
            logger.log('Activated Candidate Search View');
        }

        function init() {
            //
        }
    }
})();
