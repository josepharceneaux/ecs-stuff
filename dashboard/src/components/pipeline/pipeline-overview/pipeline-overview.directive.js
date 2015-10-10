(function () {

    'use strict';

    angular.module('app.pipeline')
        .directive('gtPipelineOverview', directiveFunction)
        .controller('PipelineOverviewController', ControllerFunction);


    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/pipeline/pipeline-overview/pipeline-overview.html',
            scope: {
            },
            controller: 'PipelineOverviewController',
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
            logger.log('Activated Pipeline Overview View');
        }
    }

})();
