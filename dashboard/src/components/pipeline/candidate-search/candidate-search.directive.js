(function () {

    'use strict';

    angular.module('app.pipeline')
        .directive('gtCandidateSearch', directiveFunction)
        .controller('CandidateSearchController', ControllerFunction);


    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/pipeline/candidate-search/candidate-search.html',
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
