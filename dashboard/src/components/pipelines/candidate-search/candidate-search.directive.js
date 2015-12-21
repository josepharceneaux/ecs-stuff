(function () {

    'use strict';

    angular.module('app.pipelines')
        .directive('gtCandidateSearch', directiveFunction)
        .controller('CandidateSearchController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/pipelines/candidate-search/candidate-search.html',
            replace: true,
            scope: {
            },
            controller: 'CandidateSearchController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['logger'];

    /* @ngInject */
    function ControllerFunction(logger) {

        activate();

        function activate() {
            logger.log('Activated Candidate Search View');
        }
    }
})();