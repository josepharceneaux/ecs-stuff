// -------------------------------------
//   Line Graph
//   ->
// -------------------------------------

(function () {
    'use strict';

    angular
        .module('app.core')
        .directive('gtCandidateGrowthGraph', directiveFunction)
        .controller('CandidateGrowthGraphController', ControllerFunction)

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'AE',
            require: ['gtCandidateGrowthGraph'],
            templateUrl: 'core/modules/d3/candidate-growth-graph/candidate-growth-graph.html',
            replace: true,
            scope: {
                pipelineId: '='
            },
            controller: 'CandidateGrowthGraphController',
            controllerAs: 'candidateGrowthGraph',
            bindToController: true,
            link: linkFunction
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = [];

    /* @ngInject */
    function ControllerFunction() {
        var vm = this;
    }

    function linkFunction(scope, elem, attrs, ctrls) {
        //
    }

})();
