(function () {

    'use strict';

    angular.module('app.pipeline')
        .directive('gtPipeline', directiveFunction)
        .controller('PipelineController', ControllerFunction);


    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/pipeline/pipeline.html',
            scope: {
            },
            controller: 'PipelineController',
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
            logger.log('Activated Pipeline View');
        }
    }

})();
