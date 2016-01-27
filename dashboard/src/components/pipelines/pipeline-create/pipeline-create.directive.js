(function () {
    'use strict';

    angular.module('app.pipelines')
        .directive('gtPipelineCreate', directiveFunction)
        .controller('PipelineCreateController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/pipelines/pipeline-create/pipeline-create.html',
            replace: true,
            scope: {},
            controller: 'PipelineCreateController',
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
            logger.log('Activated Pipeline Create View');
        }

        function init() {
            //
        }
    }
})();
